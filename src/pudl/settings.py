"""Module for validating pudl etl settings."""
import abc
from typing import Any, ClassVar, Dict, List

import pandas as pd
from pydantic import BaseModel as PydanticBaseModel
from pydantic import root_validator, validator

import pudl.constants as pc
from pudl.extract.ferc1 import DBF_TABLES_FILENAMES
from pudl.metadata.enums import EPACEMS_STATES


class BaseModel(PydanticBaseModel):
    """BaseModel with global configuration."""

    class Config:
        """Pydantic config."""

        allow_mutation = False
        extra = "forbid"


class GenericDatasetSettings(BaseModel, abc.ABC):
    """
    An abstract pydantic model for generic datasets.

    Attributes:
        working_partitions ClassVar[Dict[str, List[Any]]]):
            dictionary of arbitrary working partitions.
    """

    @property
    @abc.abstractmethod
    def working_partitions(cls) -> Dict[str, List[Any]]:
        """Abstract working_partitions property."""
        return sorted(cls.working_partitions)

    @root_validator
    def validate_partitions(cls, partitions):
        """Validate partitions are available."""
        for name, working_partitions in cls.working_partitions.items():
            try:
                partition = partitions[name]
            except KeyError:
                raise ValueError(f"{cls.__name__} is missing '{name}' field.")

            partitions_not_working = list(set(partition) - set(working_partitions))
            if len(partitions_not_working) > 0:
                raise ValueError(
                    f"'{partitions_not_working}' {name} are not available.")
            partitions[name] = sorted(set(partition))
        return partitions


class Ferc1Settings(GenericDatasetSettings):
    """
    An immutable pydantic model to validate FERC1 settings.

    Attributes:
        years (List[int]): List of years to validate.
        tables (List[str]): List of table to validate.

        working_partitions ClassVar[Dict[str, Any]]: working paritions.
    """

    # TODO: import tables from resources.py
    # TODO: Move all working partition data to resources?
    working_partitions: ClassVar = {
        "tables": sorted([
            'fuel_ferc1',
            'plants_steam_ferc1',
            'plants_small_ferc1',
            'plants_hydro_ferc1',
            'plants_pumped_storage_ferc1',
            'purchased_power_ferc1',
            'plant_in_service_ferc1'
        ]),
        "years": list(pc.WORKING_PARTITIONS["ferc1"]["years"])
    }

    years: List[int] = working_partitions["years"]
    tables: List[str] = working_partitions["tables"]


class Eia860Settings(GenericDatasetSettings):
    """
    An immutable pydantic model to validate EIA860 settings.

    This model also check 860m settings.

    Attributes:
        years (List[int]): List of years to validate.
        tables (List[str]): List of table to validate.

        working_partitions ClassVar[Dict[str, Any]]: working paritions.
        eia860m_date ClassVar[str]: The 860m year to date.
    """

    working_partitions: ClassVar = {
        "tables": sorted([
            'boiler_generator_assn_eia860',
            'utilities_eia860',
            'plants_eia860',
            'generators_eia860',
            'ownership_eia860'
        ]),
        "years": list(pc.WORKING_PARTITIONS["eia860"]["years"])
    }
    eia860m_date: ClassVar[str] = '2020-11'

    years: List[int] = working_partitions["years"]
    tables: List[str] = working_partitions["tables"]
    eia860m: bool = False

    @validator("eia860m")
    def check_860m_date(cls, eia860m):
        """
        Check 860m date year is exactly one year later than most recent working 860 year.

        Args:
            eia860m (bool): True if 860m is requested.

        Returns:
            eia860m (bool): True if 860m is requested.

        Raises:
            ValueError: the 860m date is within 860 working years.
        """
        eia860m_year = pd.to_datetime(cls.eia860m_date).year
        if eia860m and (eia860m_year != max(cls.working_partitions["years"]) + 1):
            raise AssertionError(
                """Attempting to integrate an eia860m year"""
                f"""({eia860m_year}) that is within the eia860 years:"""
                f"""{cls.working_partitions["years"]}. Consider switching eia860m"""
                """parameter to False."""
            )
        return eia860m


class Eia923Settings(GenericDatasetSettings):
    """
    An immutable pydantic model to validate EIA923 settings.

    Attributes:
        years (List[int]): List of years to validate.
        tables (List[str]): List of table to validate.

        working_years (ClassVar[List[int]]): List of working years.
        working_tables (ClassVar[List[str]]): List of working table.
    """

    working_partitions: ClassVar = {
        "tables": sorted([
            'generation_fuel_eia923',
            'boiler_fuel_eia923',
            'generation_eia923',
            'coalmine_eia923',
            'fuel_receipts_costs_eia923'
        ]),
        "years": list(pc.WORKING_PARTITIONS["eia923"]["years"])
    }

    years: List[int] = working_partitions["years"]
    tables: List[str] = working_partitions["tables"]


class GlueSettings(BaseModel):
    """
    An immutable pydantic model to validate Glue settings.

    Attributes:
        eia (bool): Include eia in glue settings.
        ferc1 (bool): Include ferc1 in glue settings.
    """

    eia: bool = True
    ferc1: bool = True


class EpaCemsSettings(GenericDatasetSettings):
    """
    An immutable pydantic nodel to validate EPA CEMS settings.

    Attributes:
        states (List[str]): List of states to validate.
        years (List[str]): List of years to validate.
    """

    working_partitions: ClassVar = {
        "states": sorted(set(EPACEMS_STATES)),
        "years": list(pc.WORKING_PARTITIONS["epacems"]["years"])
    }

    years: List[int] = working_partitions["years"]
    states: List[str] = working_partitions["states"]

    @validator("states")
    def allow_all_keyword(cls, states):
        """Allow users to specify ['all'] to get all states."""
        if states == ["all"]:
            states = cls.working_partitions["states"]
        return states


class EiaSettings(BaseModel):
    """
    An immutable pydantic model to validate EIA datasets settings.

    Attributes:
        eia860 (Eia860Settings): Immutable pydantic model to validate eia860 settings.
        eia923 (Eia923Settings): Immutable pydantic model to validate eia923 settings.
    """

    eia860: Eia860Settings = None
    eia923: Eia923Settings = None

    @root_validator
    def check_eia_dependencies(cls, values):
        """
        Make sure the dependencies between the eia datasets are satisfied.

        Dependencies:
        * eia860 requires eia923.boiler_fuel_eia923 and eia923.generation_eia923.
        * eia923 requires eia860 for harvesting purposes.

        Args:
            values (Dict[str, BaseModel]): dataset settings.

        Returns:
            values (Dict[str, BaseModel]): dataset settings.
        """
        eia923 = values.get("eia923")
        eia860 = values.get("eia860")
        if not eia923 and eia860:
            values["eia923"] = Eia923Settings(
                tables=['boiler_fuel_eia923', 'generation_eia923'],
                years=eia860.years
            )

        if eia923 and not eia860:
            values["eia860"] = Eia860Settings(
                years=eia923.years
            )
        return values


class DatasetsSettings(BaseModel):
    """
    An immutable pydantic model to validate PUDL Dataset settings.

    Attributes:
        ferc1 (Ferc1Settings): Immutable pydantic model to validate ferc1 settings.
        eia (EiaSettings): Immutable pydantic model to validate eia(860, 923) settings.
        glue (GlueSettings): Immutable pydantic model to validate glue settings.
        epacems (EpaCemsSettings): Immutable pydantic model to validate epacems settings.
    """

    ferc1: Ferc1Settings = None
    eia: EiaSettings = None
    glue: GlueSettings = None
    epacems: EpaCemsSettings = None

    @root_validator(pre=True)
    def default_load_all(cls, values):
        """
        If no datasets are specified default to all.

        Args:
            values (Dict[str, BaseModel]): dataset settings.

        Returns:
            values (Dict[str, BaseModel]): dataset settings.
        """
        if not any(values.values()):
            values["ferc1"] = Ferc1Settings()
            values["eia"] = EiaSettings()
        return values

    @root_validator
    def add_glue_settings(cls, values):
        """
        Add glue settings if ferc1 and eia data are both requested.

        Args:
            values (Dict[str, BaseModel]): dataset settings.

        Returns:
            values (Dict[str, BaseModel]): dataset settings.
        """
        if values.get("ferc1") and values.get("eia"):
            values["glue"] = GlueSettings()
        return values

    def get_datasets(cls):
        """Gets dictionary of dataset settings."""
        return vars(cls)


class Ferc1ToSqliteSettings(GenericDatasetSettings):
    """
    An immutable pydantic nodel to validate EPA CEMS settings.

    Attributes:
        tables (List[str]): List of states to validate.
        years (List[str]): List of years to validate.
        refyear (int): reference year. Defaults to most recent year.
    """

    working_partitions: ClassVar = {
        "tables": sorted(list(DBF_TABLES_FILENAMES.keys())),
        "years": list(pc.WORKING_PARTITIONS["ferc1"]["years"])
    }

    years: List[int] = working_partitions["years"]
    tables: List[str] = working_partitions["tables"]

    refyear: int = max(working_partitions["years"])
    bad_cols: tuple = ()

    @validator("refyear")
    def check_reference_year(cls, refyear: int) -> int:
        """Checks reference year is within available years."""
        if refyear not in cls.working_partitions["years"]:
            raise ValueError(f"Reference year {refyear} is outside the range of "
                             f"available FERC Form 1 data {cls.working_partitions['years']}.")
        return refyear
