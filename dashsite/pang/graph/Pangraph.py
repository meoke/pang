from typing import List, Dict
import abc
from fileformats.maf.DAGMaf import DAGMaf
from metadata.MultialignmentMetadata import MultialignmentMetadata
from .Node import Node
from .PathManager import PathManager
import numpy as np
from . import nucleotides
from collections import deque


class PangraphBuilder(abc.ABC):
    @abc.abstractmethod
    def build(self, input, pangraph, genomes_info):
        pass


class EmptyIn:
    def __init__(self, to_block, node_id, seq_id, seq_pos):
        self.to_block = to_block
        self.node_id = node_id
        self.seq_id = seq_id
        self.seq_pos = seq_pos

    def __str__(self):
        return f"To: {self.to_block} " \
            f"Node_id: {self.node_id}, " \
            f"Seq_id: {self.seq_id}, Seq pos: {self.seq_pos}"


class EmptyOut:
    def __init__(self, from_block, node_id, to_block, seq_id, seq_pos, type):
        self.from_block = from_block
        self.node_id = node_id
        self.to_block = to_block
        self.seq_id = seq_id
        self.seq_pos = seq_pos
        self.type = type

    def __str__(self):
        return f"From: {self.from_block}, To: {self.to_block}, " \
            f"Type: {self.type}, Node_id: {self.node_id}, " \
            f"Seq_id: {self.seq_id}, Seq pos: {self.seq_pos}"


class SeqAttributes:
    def __init__(self, start, size):
        self.start = start
        self.size = size

    def get_last_pos(self):
        return self.start + self.size - 1

    def __str__(self):
        return f"Start: {self.start}, Size: {self.size}"


class VisitOnlyOnceDeque():
    def __init__(self, iterable):
        self.d = deque(iterable)
        self.history = []

    def append(self, element):
        if element not in self.history:
            self.d.append(element)
            self.history.append(element)

    def popleft(self):
        element = self.d.popleft()
        self.history.append(element)
        return element

    def not_empty(self):
        if len(self.d):
            return True
        return False


class PangraphBuilderFromDAG(PangraphBuilder):
    @staticmethod
    def build(input, pangraph, genomes_info: MultialignmentMetadata, fasta_source: type):
        sequences_names = genomes_info.get_all_mafnames()
        nodes_count = PangraphBuilderFromDAG.get_nodes_count(input)
        pangraph._nodes = [None] * nodes_count
        pangraph._pathmanager.init_paths(sequences_names, nodes_count)
        current_node_id = -1

        out_edges = []#to zbudować węzły, jeśli początku sekwencji nie ma w mafie (przejrzeć dag, znaleźć najmniejszy start i jeśłi jest większy niż 0 tzn że trzeba dociagac)
        #jesli byly budowane to dac id ostatniego do out edges, jesli nie to None
        in_edges = []
        blocks_deque = VisitOnlyOnceDeque([0]) #todo czy pierwszy jest rzeczywiście pierwszy?
        while blocks_deque.not_empty():
            block_id = blocks_deque.popleft()
            block = input.dagmafnodes[block_id]
            block_width = len(block.alignment[0].seq)
            sequence_name_to_parameters = {seq.id: SeqAttributes(seq.annotations["start"], seq.annotations["size"]) for seq in block.alignment}
            local_edges = {seq.id : PangraphBuilderFromDAG.get_matching_connection(out_edges, seq.id, block_id, in_edges) for seq in block.alignment}
            #sprawdzac pozycje - jesli sie nie zgadzaja to robic dobudowki śródblokowe

            for col in range(block_width):
                sequence_name_to_nucleotide = {seq.id: seq[col] for seq in block.alignment}
                nodes_codes = sorted([*(set([nucleotide for nucleotide in sequence_name_to_nucleotide.values()])).difference(set(['-']))])
                column_nodes_ids = [current_node_id + i + 1 for i, _ in enumerate(nodes_codes)]

                for i, nucl in enumerate(nodes_codes):
                    current_node_id += 1
                    node = Node(id=current_node_id,
                                base=nucleotides.code(nucl),
                                in_nodes=set(),
                                aligned_to=PangraphBuilderFromDAG.get_next_aligned_node_id(i, column_nodes_ids))

                    for sequence, nucleotide in sequence_name_to_nucleotide.items():
                        if nucleotide == nucl:
                            pangraph.add_path_to_node(path_name=sequence, node_id=current_node_id)
                            # find previous node
                            last_node_id = local_edges[sequence]
                            if last_node_id is not None:
                                node.in_nodes.add(last_node_id)
                            elif sequence_name_to_parameters[sequence].start != 0:
                                in_edges.append(EmptyIn(block_id, current_node_id, sequence, sequence_name_to_parameters[sequence].start))

                            # add this node as open if the edge
                            local_edges[sequence] = current_node_id
                    node.in_nodes = list(node.in_nodes)
                    pangraph._nodes[current_node_id] = node

            # tutaj wstawić otwarte połączenia
            for edge in block.out_edges:
                if edge.edge_type == (1,-1):
                    blocks_deque.append(edge.to)
                for seq in edge.sequences:
                    seq_end = seq[1]
                    seq_id = seq_end.seq_id
                    out_edges.append(EmptyOut(block_id, local_edges[seq_id], edge.to, seq_id, sequence_name_to_parameters[seq_id].get_last_pos(), edge.edge_type))

        in_node_to_remove = []
        out_node_to_remove = []
        for j, open_edge in enumerate(out_edges):
            for i, in_edge in enumerate(in_edges):
                if open_edge.seq_id == in_edge.seq_id and open_edge.to_block == in_edge.to_block and open_edge.seq_pos == in_edge.seq_pos -1:
                    pangraph._nodes[in_edge.node_id].in_nodes.append(open_edge.node_id)
                    pangraph._nodes[in_edge.node_id].in_nodes = sorted(pangraph._nodes[in_edge.node_id].in_nodes)
                    in_node_to_remove.append(i)
                    out_node_to_remove.append(j)
                    break
        # do koncowek dociagnac wezly
        for index in sorted(in_node_to_remove, reverse=True):
            del in_edges[index]
        for index in sorted(out_node_to_remove, reverse=True):
            del out_edges[index]
        with open("a.txt", 'w') as o:
            for i in in_edges:
                o.write(f"{i}\n")
            for i in out_edges:
                o.write(f"{i}\n")

        pangraph._pathmanager.remove_empty_paths()

    @staticmethod
    def get_nodes_count(dagmaf: DAGMaf) -> int:
        nodes_count = 0
        for n in dagmaf.dagmafnodes:
            number_of_columns = len(n.alignment[0].seq)
            for col_id in range(number_of_columns):
                letters_in_columns = set([n.alignment[i].seq[col_id] for i in range(len(n.alignment))]).difference(set('-'))
                nodes_count += len(letters_in_columns)
        return nodes_count

    @staticmethod
    def get_next_aligned_node_id(current_column_i, column_nodes_ids):
        if len(column_nodes_ids) > 1:
            return column_nodes_ids[(current_column_i + 1) % len(column_nodes_ids)]
        return None

    @staticmethod
    def get_matching_connection(out_edges, seq_id, to_block_id, in_edges):
        edge_id = None
        edge = None
        for i, freeEdge in enumerate(out_edges):
            if freeEdge.seq_id == seq_id and freeEdge.type == (1,-1) and freeEdge.to_block == to_block_id:
                for j, e in enumerate(in_edges):
                    if e.to_block == to_block_id and e.seq_id == seq_id:
                        del in_edges[j]
                edge_id = i
                edge = freeEdge
                break
        if edge_id is not None:
            del out_edges[edge_id]
            return edge.node_id
        return None

class Pangraph():
    def __init__(self):
        self._nodes = []
        self._pathmanager = PathManager()
        self._consensusmanager = PathManager()

    # def __init__(self, max_nodes_count: int=0, start_node_id: int=0, paths_names: List[str]=None):
    #     self._nodes = [None] * max_nodes_count
    #     self._pathmanager = PathManager(start_node_id, max_nodes_count, paths_names)
    #     self._consensusmanager = PathManager()

    def __eq__(self, other):
        return (self._nodes == other._nodes and
                self._pathmanager == other._pathmanager and
                self._consensusmanager == other._consensusmanager)

    def build(self, input, genomes_info):
        if isinstance(input, DAGMaf):
            builder: PangraphBuilder = PangraphBuilderFromDAG()
        builder.build(input, self, genomes_info)

    def update(self, pangraph, start_node):
        self.update_nodes(pangraph._nodes)
        self._pathmanager.update(pangraph._pathmanager, start=start_node)

    def update_nodes(self, new_nodes: List[Node]):
        #todo something to control new_nodes correctness
        if not new_nodes:
            raise Exception("empty new nodes")
        if len(self._nodes) <= new_nodes[-1].id:
            self._nodes = new_nodes
            return
        self._nodes[new_nodes[0].id: new_nodes[-1].id] = new_nodes

    def get_nodes_count(self):
        return len(self._nodes)

    def get_nodes(self):
        return self._nodes

    def trim_nodes(self, nodes_count: int):
        del self._nodes[nodes_count:]
        self._pathmanager.trim(nodes_count)

    def set_paths(self, max_nodes_count: int, paths_to_node_ids: Dict[str, List[int]] = None):
        # todo something to control paths correctness
        self._pathmanager.init_from_dict(max_nodes_count, paths_to_node_ids)

    def add_path_to_node(self, path_name, node_id):
        self._pathmanager.mark(path_name, node_id)

    def get_in_nodes(self, node_id):
        return self._pathmanager.get_in_nodes(node_id)

    # def add_node(self, node: Node, node_id: str):
    #     self._nodes[node_id] = node

    def fill_in_nodes(self):
        for node in self._nodes:
            node.in_nodes = self.get_in_nodes(node.id)

    def get_paths_count(self):
        return self._pathmanager.get_paths_count()

    def get_path_names(self):
        return self._pathmanager.get_path_names()

    def get_path_ids(self):
        return self._pathmanager.get_path_ids()

    def get_path_id(self, pathname):
        return self._pathmanager.get_path_id(pathname)

    def get_path_nodes_count(self, pathname):
        return self._pathmanager.get_path_nodes_count(pathname)

    def get_start_node_id(self, source):
        return self._pathmanager.get_start_node_id(source)

    def get_sources_weights_dict(self):
        return self._pathmanager.get_sources_weights_dict()

    def get_source_consensus_id(self, source):
        return -1

    def get_sources_ids(self, node_id: int) -> List[int]:
        return self._pathmanager.get_sources_ids(node_id)

    def set_consensuses(self, max_nodes_count, paths_to_node_ids):
        self._consensusmanager.init_from_dict(max_nodes_count, paths_to_node_ids)

    def set_cm(self, cm):
        self._consensusmanager = cm

    def get_top_consensus(self):
        return self._consensusmanager.get_top_consensus()

    def get_node(self, node_id):
        return self._nodes[node_id]

    def remove_empty_paths(self):
        self._pathmanager.remove_empty_paths()

    def get_paths(self):
        return self._pathmanager.get_paths()

    def get_path(self, pathname):
        return self._pathmanager.get_path(pathname)

    def get_path_compatibility(self, path, consensus):
        common_nodes_count = np.sum(path & consensus)
        source_nodes_count = np.sum(path)
        return round(common_nodes_count / source_nodes_count, 3)
        # return common_nodes_count / source_nodes_count

    def get_paths_compatibility(self, consensus_id):
        consensus = self._consensusmanager.paths[consensus_id]
        return [self.get_path_compatibility(path, consensus) for path in self._pathmanager.paths]

    def get_paths_compatibility_to_consensus(self, consensus):
        return {self._pathmanager.get_path_name(path_id): self.get_path_compatibility(path, consensus)
                for path_id, path in enumerate(self._pathmanager.paths)}

    def add_consensus(self, consensus):
        self._consensusmanager.add_path("CONSENSUS", consensus)

    def get_source_name(self, src_id):
        return self._pathmanager.get_path_name(src_id)

    def clear_consensuses(self):
        self._consensusmanager.clear_paths()

    def set_consensus_manager(self, consensus_manager):
        self._consensusmanager = consensus_manager

    def get_sequence_nodes_ids(self, sequence):
        return self._pathmanager.get_nodes_ids(sequence)

    def get_consensus_nodes_ids(self, sequence):
        return self._consensusmanager.get_nodes_ids(sequence)
