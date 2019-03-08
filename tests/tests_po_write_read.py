import unittest
from ddt import ddt, data, unpack
from pathlib import Path
from typing import List

from tests.context import Pangraph
from tests.context import Node
from tests.context import nucleotides as n
from tests.context import powriter
from tests.context import poreader
from tests.context import pathtools
from tests.context import MultialignmentMetadata
from tests.context import SequenceMetadata
import tests.helper_show_diffs as diff


def get_pangraph1() -> (Pangraph, List[str]):
    nodes = [Node(id=0, base=n.code('A'), in_nodes=[], aligned_to=1),
             Node(id=1, base=n.code('G'), in_nodes=[], aligned_to=0),
             Node(id=2, base=n.code('C'), in_nodes=[0, 1], aligned_to=3),
             Node(id=3, base=n.code('G'), in_nodes=[], aligned_to=2),
             Node(id=4, base=n.code('A'), in_nodes=[2, 3], aligned_to=5),
             Node(id=5, base=n.code('T'), in_nodes=[2], aligned_to=4),
             Node(id=6, base=n.code('G'), in_nodes=[4, 5], aligned_to=None),
             Node(id=7, base=n.code('G'), in_nodes=[6], aligned_to=None),
             Node(id=8, base=n.code('A'), in_nodes=[7], aligned_to=9),
             Node(id=9, base=n.code('C'), in_nodes=[7], aligned_to=10),
             Node(id=10, base=n.code('G'), in_nodes=[7], aligned_to=11),
             Node(id=11, base=n.code('T'), in_nodes=[7], aligned_to=8),
             Node(id=12, base=n.code('A'), in_nodes=[8, 10], aligned_to=13),
             Node(id=13, base=n.code('C'), in_nodes=[11], aligned_to=12),
             Node(id=14, base=n.code('T'), in_nodes=[12, 13], aligned_to=None),
             Node(id=15, base=n.code('A'), in_nodes=[14], aligned_to=16),
             Node(id=16, base=n.code('C'), in_nodes=[14], aligned_to=17),
             Node(id=17, base=n.code('G'), in_nodes=[14], aligned_to=15)
             ]

    paths_to_node_ids = {
        'testseq0': [0, 2, 4, 6, 7, 8, 12, 14, 16],
        'testseq1': [1, 2, 5, 6, 7, 9],
        'testseq2': [3, 4, 6, 7, 10, 12, 14, 17],
        'testseq3': [11, 13, 14, 15]
    }
    pangraph = Pangraph()
    pangraph.update_nodes(nodes)
    pangraph.set_paths(len(nodes), paths_to_node_ids)

    expected_pofile = ["VERSION=October",
                       "NAME=test01",
                       "TITLE=test01",
                       "LENGTH=18",
                       "SOURCECOUNT=4",
                       "SOURCENAME=testseq0",
                       "SOURCEINFO=9 0 100 -1 testseq0",
                       "SOURCENAME=testseq1",
                       "SOURCEINFO=6 1 66 -1 testseq1",
                       "SOURCENAME=testseq2",
                       "SOURCEINFO=8 3 100 -1 testseq2",
                       "SOURCENAME=testseq3",
                       "SOURCEINFO=4 11 0 -1 testseq3",
                       "a:S0A1",
                       "g:S1A0",
                       "c:L0L1S0S1A3",
                       "g:S2A2",
                       "a:L2L3S0S2A5",
                       "t:L2S1A4",
                       "g:L4L5S0S1S2",
                       "g:L6S0S1S2",
                       "a:L7S0A9",
                       "c:L7S1A10",
                       "g:L7S2A11",
                       "t:L7S3A8",
                       "a:L8L10S0S2A13",
                       "c:L11S3A12",
                       "t:L12L13S0S2S3",
                       "a:L14S3A16",
                       "c:L14S0A17",
                       "g:L14S2A15"]

    return pangraph, expected_pofile

def get_pangraph_with_consensuses() -> (Pangraph, List[str]):
    nodes = [Node(id=0, base=n.code('C'), in_nodes=[], aligned_to=1),
             Node(id=1, base=n.code('T'), in_nodes=[], aligned_to=0),
             Node(id=2, base=n.code('A'), in_nodes=[1], aligned_to=3),
             Node(id=3, base=n.code('G'), in_nodes=[0], aligned_to=2),
             Node(id=4, base=n.code('C'), in_nodes=[2, 3], aligned_to=None),
             Node(id=5, base=n.code('T'), in_nodes=[4], aligned_to=None),
             Node(id=6, base=n.code('A'), in_nodes=[5], aligned_to=7),
             Node(id=7, base=n.code('T'), in_nodes=[5], aligned_to=6),
             Node(id=8, base=n.code('G'), in_nodes=[6, 7], aligned_to=None),
             ]

    sequences_paths_to_node_ids = {
        'testseq0': [0, 3, 4, 5, 6, 8],
        'testseq1': [1, 2, 4, 5, 7, 8]
    }
    consensuses_paths_to_node_ids = {
        'CONSENS0': [0, 3, 4, 5, 7, 8],
        'CONSENS1': [1, 2, 4, 5, 6, 8]
    }
    pangraph = Pangraph()
    pangraph.update_nodes(nodes)
    pangraph.set_paths(len(nodes), sequences_paths_to_node_ids)
    pangraph.set_consensuses(len(nodes), consensuses_paths_to_node_ids)

    expected_pofile = ["VERSION=October",
                       "NAME=test01",
                       "TITLE=test01",
                       "LENGTH=9",
                       "SOURCECOUNT=4",
                       "SOURCENAME=testseq0",
                       "SOURCEINFO=6 0 100 0 testseq0",
                       "SOURCENAME=testseq1",
                       "SOURCEINFO=6 1 100 1 testseq1",
                       "SOURCENAME=CONSENS0",
                       "SOURCEINFO=6 0 -1 0 CONSENS0",
                       "SOURCENAME=CONSENS1",
                       "SOURCEINFO=6 1 -1 1 CONSENS1",
                       "c:S0S2A1",
                       "t:S1S3A0",
                       "a:L1S1S3A3",
                       "g:L0S0S2A2",
                       "c:L2L3S0S1S2S3",
                       "t:L4S0S1S2S3",
                       "a:L5S0S3A7",
                       "t:L5S1S2A6",
                       "g:L6L7S0S1S2S3"]

    return pangraph, expected_pofile

@ddt
class PoWriteReadTest(unittest.TestCase):

    def setUp(self):
        self.output_dir = pathtools.create_child_dir(Path.cwd(), "po_reader_writer_tests", True)
        genomes_metadata = {0: SequenceMetadata(name="testseq0"),
                            1: SequenceMetadata(name="testseq1"),
                            2: SequenceMetadata(name="testseq2"),
                            3: SequenceMetadata(name="testseq3")}
        self.genomes_info = MultialignmentMetadata(title="test01",
                                                   version="October",
                                                   genomes_metadata=genomes_metadata)
        self.remove_temp_dir = True

    @data((get_pangraph1()[0], get_pangraph1()[1]))
    @unpack
    def test_write_po(self, pangraph, expected_pofile):
        poa_path = pathtools.get_child_file_path(self.output_dir, "saved_pangraph.po")
        powriter.save(pangraph, poa_path, self.genomes_info)
        with open(poa_path) as poa_file:
            actual_pofile = poa_file.read().splitlines()
        try:
            self.assertListEqual(expected_pofile, actual_pofile)
            self.remove_temp_dir = True
        except Exception as ex:
            self.remove_temp_dir = False
            raise ex

    @data((get_pangraph1()[0], get_pangraph1()[1]),
          (get_pangraph_with_consensuses()[0], get_pangraph_with_consensuses()[1]))
    @unpack
    def test_read_po(self, expected_pangraph, pofile_lines):
        poa_path = pathtools.get_child_file_path(self.output_dir, "pangraph_to_read.po")
        with open(poa_path, 'w') as poa_file:
            poa_file.writelines("\n".join(pofile_lines))

        actual_pangraph = poreader.read(poa_path)
        try:
            self.compare_pangraphs(actual_pangraph=actual_pangraph, expected_pangraph=expected_pangraph)
            self.remove_temp_dir = True
        except Exception as ex:
            self.remove_temp_dir = False
            raise ex


    @data(([], ""),
          ([0, 1], "L0L1"))
    @unpack
    def test_get_in_nodes_info(self, in_nodes, expected_info):
        node = Node(id=0, base=0, in_nodes=in_nodes, aligned_to=None)
        actual_in_nodes_info = powriter.get_in_nodes_info(node)

        self.assertEqual(actual_in_nodes_info, expected_info)

    @data(([], ""),
          ([0, 1], "S0S1"),
          ([1, 3], "S1S3"))
    @unpack
    def test_get_sources_info(self, sources_ids, expected_info):
        actual_sources_info = powriter.get_sources_info(sources_ids)

        self.assertEqual(actual_sources_info, expected_info)

    @data((None, ""),
          (0, "A0"))
    @unpack
    def test_get_aligned_to_info(self, aligned_to, expected_aligned_to):
        node = Node(id=0, base=0, in_nodes=[], aligned_to=aligned_to)
        actual_aligned_to_info = powriter.get_aligned_to_info(node)

        self.assertEqual(actual_aligned_to_info, expected_aligned_to)


    def compare_pangraphs(self, actual_pangraph, expected_pangraph):
        try:
            self.assertEqual(actual_pangraph, expected_pangraph)
        except Exception as ex:
            diff.show_pangraph_differences(actual_pangraph=actual_pangraph, expected_pangraph=expected_pangraph)
            raise ex

    def tearDown(self):
        if self.remove_temp_dir:
            pathtools.remove_dir(self.output_dir)





if __name__ == '__main__':
    unittest.main()
