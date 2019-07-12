import os
import sys
import datetime

from pangtreebuild.datamodel.fasta_providers.ConstSymbolProvider import ConstSymbolProvider

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../pangtreebuild')))
from pangtreebuild.consensus import tree_generator, simple_tree_generator
from pangtreebuild.datamodel.input_types import Maf, Po
from pangtreebuild.datamodel.Poagraph import Poagraph
from pangtreebuild.tools import cli, pathtools, logprocess
from pangtreebuild.output.PangenomeJSON import to_PangenomeJSON, TaskParameters, to_json, to_pickle, load_pickle, str_to_PangenomeJSON
from pangtreebuild.output.PangenomePO import poagraph_to_PangenomePO
from pangtreebuild.output.PangenomeFASTA import poagraph_to_fasta, consensuses_tree_to_fasta


def main():
    parser = cli.get_parser()
    args = parser.parse_args()

    start = datetime.datetime.now()
    if not args.quiet and args.verbose:
        logprocess.add_file_handler_to_logger(args.output_dir, "details", "details.log", propagate=False)
        logprocess.add_file_handler_to_logger(args.output_dir, "", "details.log", propagate=False)
    if args.quiet:
        logprocess.disable_all_loggers()

    poagraph, dagmaf, fasta_provider = None, None, None
    if isinstance(args.multialignment, Maf) and args.raw_maf:
        poagraph = Poagraph.build_from_maf(args.multialignment, args.metadata)
    elif isinstance(args.multialignment, Maf) and not args.raw_maf:
        fasta_provider = cli.resolve_fasta_provider(args)
        poagraph, dagmaf = Poagraph.build_from_dagmaf(args.multialignment, fasta_provider, args.metadata)
    elif isinstance(args.multialignment, Po):
        poagraph = Poagraph.build_from_po(args.multialignment, args.metadata)

    if args.consensus is not None:
        blosum = args.blosum if args.blosum else cli.get_default_blosum()
        if fasta_provider is not None and isinstance(fasta_provider, ConstSymbolProvider):
            blosum.check_if_symbol_is_present(fasta_provider.missing_symbol.as_str())

        consensus_output_dir = pathtools.get_child_dir(args.output_dir, "consensus")
        consensus_tree = None
        if args.consensus == 'poa':
            consensus_tree = simple_tree_generator.get_simple_consensus_tree(poagraph,
                                                                             blosum,
                                                                             consensus_output_dir,
                                                                             args.hbmin,
                                                                             args.verbose)
        elif args.consensus == 'tree':
            max_strategy = cli.resolve_max_strategy(args)
            node_strategy = cli.resolve_node_strategy(args)
            consensus_tree = tree_generator.get_consensus_tree(poagraph,
                                                               blosum,
                                                               consensus_output_dir,
                                                               args.stop,
                                                               args.p,
                                                               max_strategy,
                                                               node_strategy,
                                                               args.verbose)
    end = datetime.datetime.now()
    if args.output_po:
        pangenome_po = poagraph_to_PangenomePO(poagraph)
        pathtools.save_to_file(pangenome_po, pathtools.get_child_path(args.output_dir, "poagraph.po"))

    if args.output_fasta:
        sequences_fasta = poagraph_to_fasta(poagraph)
        pathtools.save_to_file(sequences_fasta, pathtools.get_child_path(args.output_dir, "sequences.fasta"))
        if consensus_tree:
            consensuses_fasta = consensuses_tree_to_fasta(poagraph, consensus_tree)
            pathtools.save_to_file(consensuses_fasta, pathtools.get_child_path(args.output_dir, "consensuses.fasta"))


    pangenomejson = to_PangenomeJSON(task_parameters=cli.get_task_parameters(args, running_time=f"{end-start}s"),
                                     poagraph=poagraph,
                                     dagmaf=dagmaf,
                                     consensuses_tree=consensus_tree)
    pangenome_json_str = to_json(pangenomejson)
    pathtools.save_to_file(pangenome_json_str, pathtools.get_child_path(args.output_dir, "pangenome.json"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exp:
        print("Something went wrong...")
        raise exp
