import datetime

from babel import Locale as LC
from babel.dates import format_datetime
from babel.units import format_unit
print(u'15.\u201317.1.2016')

startTime = datetime.timedelta(4, 54915)
startTime = (datetime.datetime.min + startTime)
test = LC('de')
print(test.number_symbols)
print(format_unit(12, 'duration-day', length="short", locale='de'))
print(format_datetime(startTime, locale='de'))
