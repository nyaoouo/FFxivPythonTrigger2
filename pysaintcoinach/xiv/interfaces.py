from abc import abstractmethod
from typing import Iterable
from .. import text


class IItemSource(object):
    """
    Interface for objects from which `Item`s can be obtained.
    """

    @property
    @abstractmethod
    def items(self):
        """
        Gets the `Item`s that can be obtained from the current object.
        :return: The `Item`s that can be obtained from the current object.
        """
        pass


class ILocation(object):
    """
    Interface for objects defining a location in a zone (in map-coordinates).
    """

    @property
    @abstractmethod
    def map_x(self) -> float:
        pass

    @property
    @abstractmethod
    def map_y(self) -> float:
        pass

    @property
    @abstractmethod
    def place_name(self) -> 'PlaceName':
        pass


class ILocatable(object):
    """
    Interface for objects that have specific locations.
    """

    @property
    @abstractmethod
    def locations(self) -> Iterable[ILocation]:
        """
        Gets the locations of the current object.
        :return: The locations of the current object.
        """
        pass


class IShop(IItemSource):
    """
    Interface for shops.
    """

    @property
    @abstractmethod
    def key(self) -> int:
        """
        Gets the key of the current shop.
        :return: The key of the current shop.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Gets the name of the current shop.
        :return: The name of the current shop.
        """
        pass

    @property
    @abstractmethod
    def enpcs(self) -> 'Iterable[ENpc]':
        """
        Gets the ENpcs offering the current shop.
        :return: The ENpcs offering the current shop.
        """
        pass

    @property
    @abstractmethod
    def shop_listings(self) -> 'Iterable[IShopListing]':
        """
        Gets the listings of the current shop.
        :return: The listings of the current shop.
        """
        pass


class IShopListing(object):
    """
    Interface for listing of shops.
    """

    @property
    @abstractmethod
    def rewards(self) -> 'Iterable[IShopListingItem]':
        """
        Gets the rewards of the current listing.
        :return: The rewards of the current listing.
        """
        pass

    @property
    @abstractmethod
    def costs(self) -> 'Iterable[IShopListingItem]':
        """
        Gets the costs of the current listing.
        :return: The costs of the current listing.
        """
        pass

    @property
    @abstractmethod
    def shops(self) -> 'Iterable[IShop]':
        """
        Gets the shops offering the current listing.
        :return: The shops offering the current listing.
        """
        pass


class IShopListingItem(object):
    """
    Interface for items used in a IShopListing.
    """

    @property
    @abstractmethod
    def item(self) -> 'Item':
        """
        Gets the item of the current listing entry.
        :return: The item of the current listing entry.
        """
        pass

    @property
    @abstractmethod
    def count(self) -> int:
        """
        Gets the count for the current listing entry.
        :return: The count for the current listing entry.
        """
        pass

    @property
    @abstractmethod
    def is_hq(self) -> bool:
        """
        Gets a value indicating whether the item is high-quality.
        :return: A value indicating whether the item is high-quality.
        """
        pass

    @property
    @abstractmethod
    def collectability_rating(self) -> int:
        """
        Gets the collectability rating for the item.
        """
        pass

    @property
    @abstractmethod
    def shop_item(self) -> 'IShopListing':
        """
        Gets the IShopListing the current entry is for.
        :return: The IShopListing the current entry is for.
        """
        pass


class IQuantifiable(object):

    @property
    @abstractmethod
    def singular(self) -> str:
        pass

    @property
    @abstractmethod
    def plural(self) -> str:
        pass


class IQuantifiableXivString(IQuantifiable):

    @property
    @abstractmethod
    def singular(self) -> text.XivString:
        pass

    @property
    @abstractmethod
    def plural(self) -> text.XivString:
        pass
