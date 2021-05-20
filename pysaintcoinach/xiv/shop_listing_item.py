from .interfaces import IShopListing, IShopListingItem


class ShopListingItem(IShopListingItem):
    """
    General-purpose class for items to use in IShopListing.
    """

    def __init__(self,
                 shop_item: IShopListing,
                 item: 'Item',
                 count: int,
                 is_hq: bool,
                 collectability_rating: int):
        """
        Initializes a new instance of the ShopListingItem class.
        :param shop_item: The IShopListing the entry is for.
        :param item: The item of the entry.
        :param count: The count for the entry.
        :param is_hq: A value indicating whether the `item` is high-quality.
        :param collectability_rating: The collectability rating of the entry.
        """
        self.__shop_item = shop_item
        self.__item = item
        self.__count = count
        self.__is_hq = is_hq
        self.__collectability_rating = collectability_rating

    @property
    def shop_item(self) -> IShopListing:
        return self.__shop_item

    @property
    def item(self) -> 'Item':
        return self.__item

    @property
    def count(self) -> int:
        return self.__count

    @property
    def is_hq(self) -> bool:
        return self.__is_hq

    @property
    def collectability_rating(self) -> int:
        return self.__collectability_rating

    def __str__(self):
        result = ''
        if self.count > 1:
            result += '{0} '.format(self.count)
        result += str(self.item)
        if self.is_hq:
            result += ' (HQ)'
        return result

    def __repr__(self):
        return str(self)
