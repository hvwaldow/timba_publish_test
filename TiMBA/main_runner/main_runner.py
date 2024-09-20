from timeit import default_timer
from TiMBA.logic.model import TiMBA
from TiMBA.parameters import get_results_writer, get_global_paths, get_pkl_paths, get_output_paths
# TODO reactivate and verify if time_stamp and world_version are transfered in output names
# TODO check if all paths for outputs are provided
from TiMBA.parameters import FOREST_OUTPUT, RESULTS_OUTPUT, RESULTS_OUTPUT_AGG, WORLD_PRICE_OUTPUT
from TiMBA.data_management.ParameterCollector import ParameterCollector
from TiMBA.results_logging.base_logger import get_logger
from TiMBA.data_management.DataManager import DataManager
from TiMBA.data_management.DataContainer import WorldDataCollector, DataContainer, AdditionalInformation
from TiMBA.parameters.Defines import SolverParameters
import os


def main(UserIO: ParameterCollector, world_version: list, time_stamp: str, package_dir, sc_name: str):
    """
    Main function of TiMBA. The function is structured as follow: (1) The read in of input data and the model setup,
    (2) the computation, (3) the extraction of the model outputs.
    :param UserIO: Collection of parameters. Default calls values from TiMBA.user_io.default_parameters. Default values
     are overwritten by CLI input or different call from TiMBA.main.py
    :param world_version: Name of the input world
    :param time_stamp: Time stamp of the model start
    :param package_dir: Path of the packages directory
    :param sc_name: Name of the scenario based on the name of the input world
    """
    start = default_timer()
    # TODO removal of ResultHandler/ move to analysis toolbox
    ResultsHandler = get_results_writer(UserIO.folderpath, agg_flag=False)
    ResultsHandlerAgg = get_results_writer(UserIO.folderpath, agg_flag=True)
    # TODO remove until here
    Logger = get_logger(UserIO.folderpath)

    input_world_path, add_info_path, world_price_path = get_global_paths(UserIO.folderpath, world_version)
    WorldDataContent = WorldDataCollector(input_world_path)
    AddInfoContent = AdditionalInformation(add_info_path)
    WorldPriceContent = DataContainer(world_price_path)
    OUTPUT_PATH, latest_file, PKL_OUTPUT_PATH = get_output_paths(package_dir, time_stamp, sc_name)

    # TODO rebase name for serialization_flag
    if not UserIO.serialization or (not os.path.exists(get_pkl_paths(UserIO.folderpath)[0])):
        Logger.info(f"World.xlsx from: {input_world_path}")
        Logger.info(f"WorldPrice.xlsx from: {world_price_path}")
        Logger.info(f"AddInfo.xlsx from: {add_info_path}")
        DataManager.readin_preprocess(WorldData=WorldDataContent,
                                      AdditionalInfo=AddInfoContent,
                                      WorldPrices=WorldPriceContent,
                                      UserOptions=UserIO,
                                      Logger=Logger)
        Logger.info(f"Readin + Pre-Processing complete.")
        Logger.info(f"Input Data prepared for serialization")
        pkl_world_path, pkl_add_info_path, pkl_worldprice_path = get_pkl_paths(UserIO.folderpath)
        DataManager.serialize_to_pickle(WorldDataContent, pkl_world_path)
        DataManager.serialize_to_pickle(AddInfoContent, pkl_add_info_path)
        DataManager.serialize_to_pickle(WorldPriceContent, pkl_worldprice_path)
    else:
        Logger.info(f"Restore serialized Input Data")
        pkl_world_path, pkl_add_info_path, pkl_worldprice_path = get_pkl_paths(UserIO.folderpath)
        Logger.info(f"World.pkl from: {pkl_world_path}")
        Logger.info(f"WorldPrice.pkl from: {pkl_worldprice_path}")
        Logger.info(f"AddInfo.pkl from: {pkl_add_info_path}")
        WorldDataContent = DataManager.restore_from_pickle(pkl_world_path)
        AddInfoContent = DataManager.restore_from_pickle(pkl_add_info_path)
        WorldPriceContent = DataManager.restore_from_pickle(pkl_worldprice_path)
        DataManager.verify_base_year(WorldDataContent, UserIO, Logger)
    
    Model = TiMBA(Data=WorldDataContent, UserOptions=UserIO, AdditionalInfo=AddInfoContent,
                  WorldPriceData=WorldPriceContent, LogHandler=Logger, ResultHandler=ResultsHandler)
    # Computation
    Model.compute(max_iteration=SolverParameters.MAX_ITERATION.value,
                  rel_accuracy=SolverParameters.REL_ACCURACY.value,
                  abs_accuracy=SolverParameters.ABS_ACCURACY.value,
                  dynamization_activated=UserIO.dynamization_activated,
                  constants=UserIO.constants,
                  capped_prices=UserIO.capped_prices)
    # Output
    print()
    Logger.info(f"Save optimization results")
    output_path = {"output_path": OUTPUT_PATH, "pkl_output_path": PKL_OUTPUT_PATH}

    DataManager.save_model_output(model_data=Model.Data,
                                  time_stamp=time_stamp,
                                  world_version=world_version,
                                  logger=Logger,
                                  output_path=output_path)

    Logger.info(f"Computing TiMBA complete")
    duration = round(default_timer() - start, 3)
    Logger.info(f"TiMBA Duration: {duration} s | {round(duration / 60, 3)} min | {round(duration / 3600, 3)} h.")
