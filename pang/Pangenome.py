import metadata.reader
from .graph import mafreader
import consensus_algorithm.simple as consensussimple
import consensus_algorithm.tree as consensustree
from .consensus_algorithm.TreeConfig import TreeConfig
from fileformat.json import writer as jsonwriter


class Pangenome:
    def __init__(self, multialignment_file, data_file):
        self.genomes_info = self._read_genomes_info(data_file)
        self.pangraph = None
        self._build_graph(multialignment_file)

    def generate_fasta_files(self, output_dir):
        pass

    def generate_consensus(self, output_dir, consensus_type, hbmin, r, multiplier, stop):
        if consensus_type == 'simple':
            self.pangraph = consensussimple.run(output_dir, self.pangraph, hbmin, self.genomes_info)
        elif consensus_type == 'tree':
            tree_config = TreeConfig(hbmin=hbmin, r=r, multiplier=multiplier, stop=stop)
            self.pangraph = consensustree.run(output_dir, self.pangraph, tree_config, self.genomes_info)
        jsonwriter.save(output_dir, self.pangraph, self.genomes_info)

    def generate_visualization(self, output_dir):
        pass

    def _read_genomes_info(self, data_file):
        return metadata.reader.read(data_file)

    def _build_graph(self, multialignment_file):
        self.pangraph = mafreader.read(multialignment_file, self.genomes_info)
