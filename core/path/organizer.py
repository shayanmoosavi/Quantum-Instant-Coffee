from typing import Dict, List

from core.path import PathBuildingContext, CalculationType


class StructuredPathOrganizer:
    """
    Organizes paths into the structured format expected by the application.

    Attributes:
        INPUT_PATH_KEYS (List[str]): Keys for input paths.
        OUTPUT_PATH_KEYS (List[str]): Keys for output paths.
    """

    INPUT_PATH_KEYS = [
        "relax_input_paths", "vc_relax_input_paths", "scf_input_paths",
        "pw_bands_input_paths", "kpdos_input_paths", "bands_input_paths",
        "nscf_input_paths", "pdos_input_paths", "nscf_wannier_input_paths",
        "pw2wan_input_paths", "wannier_input_paths"
    ]

    OUTPUT_PATH_KEYS = [
        "scf_output_paths", "pw_bands_output_paths", "kpdos_output_paths",
        "projbands_paths", "bands_paths", "nscf_output_paths",
        "pdos_output_paths", "nscf_wannier_output_paths", "wannier_bands_paths"
    ]

    def organize_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                       context: PathBuildingContext) -> Dict[str, List[str]]:
        """
        Organizes raw paths into a structured format based on the context.

        Args:
            raw_paths (Dict[str, Dict[str, List[str]]]): Raw paths grouped by calculation type.
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            Dict[str, List[str]]: Structured paths grouped by input or output keys.
        """
        if context.is_input:
            return self._organize_input_paths(raw_paths, context)
        else:
            return self._organize_output_paths(raw_paths, context)

    def _organize_input_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                              context: PathBuildingContext) -> Dict[str, List[str]]:
        """
        Organizes input paths into a structured format.

        Args:
            raw_paths (Dict[str, Dict[str, List[str]]]): Raw input paths grouped by calculation type.
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            Dict[str, List[str]]: Structured input paths grouped by keys.
        """
        structured = {key: [] for key in self.INPUT_PATH_KEYS}

        # Remove wannier paths if stress is included
        if context.include_stress:
            for key in ["nscf_wannier_input_paths", "pw2wan_input_paths", "wannier_input_paths"]:
                structured.pop(key, None)

        for calc_name, file_paths in raw_paths.items():
            try:
                calc_type = CalculationType(calc_name)
            except ValueError:
                continue

            self._add_input_paths_for_calculation(structured, calc_type, file_paths, context)

        return {key: value for key, value in structured.items() if value}

    def _organize_output_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                               context: PathBuildingContext) -> Dict[str, List[str]]:
        """
        Organizes output paths into a structured format.

        Args:
            raw_paths (Dict[str, Dict[str, List[str]]]): Raw output paths grouped by calculation type.
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            Dict[str, List[str]]: Structured output paths grouped by keys.
        """
        structured = {key: [] for key in self.OUTPUT_PATH_KEYS}

        for calc_name, file_paths in raw_paths.items():
            try:
                calc_type = CalculationType(calc_name)
            except ValueError:
                continue

            self._add_output_paths_for_calculation(structured, calc_type, file_paths, context)

        return {key: value for key, value in structured.items() if value}

    @staticmethod
    def _add_output_paths_for_calculation(structured: Dict[str, List[str]],
                                          calc_type: CalculationType,
                                          file_paths: Dict[str, List[str]],
                                          context: PathBuildingContext):
        """
        Adds output paths for a specific calculation type to the structured format.

        Args:
            structured (Dict[str, List[str]]): The structured output paths.
            calc_type (CalculationType): The type of calculation.
            file_paths (Dict[str, List[str]]): Raw file paths for the calculation type.
            context (PathBuildingContext): The context containing project configuration and settings.
        """
        if calc_type in [CalculationType.SCF, CalculationType.SCF_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                if "scf_output" in file_paths:
                    structured["scf_output_paths"].extend(file_paths["scf_output"])

        elif calc_type == CalculationType.STRAIN and context.include_stress:
            path_mapping = {
                "scf_output": "scf_output_paths",
                "pw_bands_output": "pw_bands_output_paths",
                "kpdos_output": "kpdos_output_paths",
                "projbands_output": "projbands_paths",
                "bands_gnu": "bands_paths"
            }
            for file_type, struct_key in path_mapping.items():
                if file_type in file_paths:
                    structured[struct_key].extend(file_paths[file_type])

        elif calc_type in [CalculationType.PDOS, CalculationType.PDOS_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["nscf_output", "pdos_output"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.WANNIER, CalculationType.WANNIER_SOC]:
            if not context.include_stress:
                for path_type in ["nscf_wannier_output", "wannier_bands"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif not (context.include_stress and calc_type.is_soc) and calc_type not in [
            CalculationType.PDOS, CalculationType.PDOS_SOC,
            CalculationType.WANNIER, CalculationType.WANNIER_SOC
        ]:
            path_mapping = {
                "pw_bands_output": "pw_bands_output_paths",
                "kpdos_output": "kpdos_output_paths",
                "projbands_output": "projbands_paths",
                "bands_gnu": "bands_paths"
            }
            for file_type, struct_key in path_mapping.items():
                if file_type in file_paths:
                    structured[struct_key].extend(file_paths[file_type])

    @staticmethod
    def _add_input_paths_for_calculation(structured: Dict[str, List[str]],
                                         calc_type: CalculationType,
                                         file_paths: Dict[str, List[str]],
                                         context: PathBuildingContext):
        """
        Adds input paths for a specific calculation type to the structured format.

        Args:
            structured (Dict[str, List[str]]): The structured input paths.
            calc_type (CalculationType): The type of calculation.
            file_paths (Dict[str, List[str]]): Raw file paths for the calculation type.
            context (PathBuildingContext): The context containing project configuration and settings.
        """
        if calc_type in [CalculationType.SCF, CalculationType.SCF_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["relax_input", "vc_relax_input", "scf_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type == CalculationType.STRAIN and context.include_stress:
            for path_type in ["scf_input", "pw_bands_input", "kpdos_input", "bands_input"]:
                if path_type in file_paths:
                    structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.PDOS, CalculationType.PDOS_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["nscf_input", "pdos_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.WANNIER, CalculationType.WANNIER_SOC]:
            if not context.include_stress:
                for path_type in ["nscf_wannier_input", "pw2wan_input", "wannier_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif not (context.include_stress and calc_type.is_soc) and calc_type not in [
            CalculationType.WANNIER, CalculationType.WANNIER_SOC
        ]:
            for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                if path_type in file_paths and file_paths[path_type]:
                    structured[f"{path_type}_paths"].extend(file_paths[path_type])
