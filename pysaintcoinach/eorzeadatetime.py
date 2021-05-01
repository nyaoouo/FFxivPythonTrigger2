# Module with operations using the Eorzean calendar and time.
# Ported from the SaintCoinach library
# https://github.com/Rogueadyn/SaintCoinach

from datetime import datetime, timedelta, tzinfo

ZERO = timedelta(0)

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

class EorzeaDateTime(object):
    """
    Class for operations using the Eorzean calendar and time.

    One Eorzean day is 70 real-world minutes long, with zero starting at the Unix epoch (1. Jan 1970, 00:00.00).
    The Eorzean calendar is divided into Year, Moon, Sun, Bell, and Minute.
    One Year is 12 Moons.
    One Moon is 32 Suns.
    One Bell is 24 Minutes.
    """

    _zero = datetime(1970, 1, 1, tzinfo=utc)

    real_to_eorzean_factor = (60.0 * 24.0) / 70.0

    @property
    def minute(self):
        return self._minute

    @minute.setter
    def minute(self, value):
        self._minute = value
        while self._minute < 0:
            self._minute += 60
            self.bell -= 1
        while self._minute >= 60:
            self._minute -= 60
            self.bell += 1

    @property
    def bell(self):
        return self._bell;

    @bell.setter
    def bell(self, value):
        self._bell = value
        while self._bell < 0:
            self._bell += 24
            self.sun -= 1
        while self._bell >= 24:
            self._bell -= 24
            self.sun += 1

    @property
    def sun(self):
        return self._sun

    @sun.setter
    def sun(self, value):
        self._sun = value
        while self._sun < 1:
            self._sun += 32
            self.moon -= 1
        while self._sun > 32:
            self._sun -= 32
            self.moon += 1

    @property
    def moon(self):
        return self._moon

    @moon.setter
    def moon(self, value):
        self._moon = value
        while self._moon < 1:
            self._moon += 12
            self.year -= 1
        while self._moon > 12:
            self._moon -= 12
            self.year += 1

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        self._year = value

    @property
    def total_minutes(self):
        """ Gets the total amount of minutes in the Eorzean calendar since zero. """
        return self._minute + (60.0 * (self._bell + (24.0 * (self._sun + (32.0 * (self._moon + (12.0 * self._year)))))))

    @property
    def total_bells(self):
        """ Gets the total amount of bells (hours) in the Eorzean calendar since zero. """
        return self._bell + (self._minute / 60.0) + (24 * (self._sun + (32.0 * (self._moon + (12.0 * self._year)))))

    @property
    def total_suns(self):
        """ Gets the total amount of suns (days) in the Eorzean calendar since zero. """
        return self._sun + ((self._bell + (self._minute / 60.0)) / 24.0) + (32 * (self._moon + (12.0 * self._year)))

    @property
    def total_moons(self):
        """ Gets the total amount of moons (months) in the Eorzean calendar since zero. """
        return self._moon + ((self._sun + ((self._bell + (self._minute / 60.0)) / 24.0)) / 32.0) + (12.0 * self._year)

    @property
    def total_years(self):
        """ Gets the total amount of years in the Eorzean calendar since zero. """
        return self._year + ((self._moon + ((self._sun + ((self._bell + (self._minute / 60.0)) / 24.0)) / 32.0)) / 12.0)

    @classmethod
    def now(cls):
        """ Gets the current time in the Eorzean calendar. """
        eorzea_datetime = cls(1, 1, 1)
        eorzea_datetime.set_real_time(datetime.now(utc))
        return eorzea_datetime

    def clone(self):
        return self.__class__(self._year, self._moon, self._sun, self._bell, self._minute)

    def __init__(self, year, moon, sun, bell=0, minute=0):
        self._year = year
        self._moon = moon
        self._sun = sun
        self._bell = bell
        self._minute = minute

    def get_timedelta(self):
        return timedelta(days=self.sun + (((self.year * 12) + self.moon) * 32),
                         hours=self.bell,
                         minutes=self.minute)

    def get_unix_time(self):
        years = self.year
        moons = (years * 12.0) + self.moon - 1
        suns = (moons * 32.0) + self.sun - 1
        bells = (suns * 24.0) + self.bell
        minutes = (bells * 60.0) + self.minute
        seconds = minutes * 60.0
        return int(seconds / self.real_to_eorzean_factor)

    def set_unix_time(self, time):
        """ Set the Unix timestamp. """
        #print 'real_seconds = %d' % time
        eorzea_seconds = time * self.real_to_eorzean_factor
        self._set_eorzea_time(eorzea_seconds)
        return self

    def _set_eorzea_time(self, eorzea_seconds):
        """ Set the Eorzean time using the total elapsed seconds since zero. """
        #print 'eorzea_seconds = %d' % eorzea_seconds
        minutes = eorzea_seconds / 60
        #print 'minutes = %d' % minutes
        bells = minutes / 60
        #print 'bells = %d' % bells
        suns = bells / 24
        #print 'suns = %d' % suns
        moons = suns / 32
        #print 'moons = %d' % moons
        years = moons / 12
        #print 'years = %d' % years

        self.year = int(years)
        self.moon = int(moons % 12) + 1
        self.sun = int(suns % 32) + 1
        self.bell = int(bells % 24)
        self.minute = int(minutes % 60)

    def get_real_time(self):
        return self._zero + timedelta(seconds=self.get_unix_time())

    def set_real_time(self, time):
        """ Set the value of this EorzeaDateTime from a real-world datetime."""
        utc_time = time.astimezone(utc)
        from_zero = utc_time - self._zero
        return self.set_unix_time(from_zero.total_seconds())

    def __add__(self, other):
        if not isinstance(other, timedelta):
            return NotImplemented
        copy = self.clone()
        copy.minute += int(other.total_seconds() / 60.0)
        return copy

    def __sub__(self, other):
        if isinstance(other, timedelta):
            copy = self.clone()
            copy.minute -= int(other.total_seconds() / 60.0)
            return copy
        elif isinstance(other, self.__class__):
            return self.get_timedelta() - other.get_timedelta()
        else:
            return NotImplemented

    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return cmp(self.get_unix_time(), other.get_unix_time())

    def __str__(self):
        def ord(n):
            return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))
        moons = ['1st Astral Moon',
                 '1st Umbral Moon',
                 '2nd Astral Moon',
                 '2nd Umbral Moon',
                 '3rd Astral Moon',
                 '3rd Umbral Moon',
                 '4th Astral Moon',
                 '4th Umbral Moon',
                 '5th Astral Moon',
                 '5th Umbral Moon',
                 '6th Astral Moon',
                 '6th Umbral Moon']
        return 'Year %d, %s, %s Sun, %02d:%02d' % (self.year, moons[self.moon - 1], ord(self.sun), self.bell, self.minute)
