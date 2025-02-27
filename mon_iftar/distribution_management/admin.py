from django.contrib import admin

# Register your models here.
from .models import (
    Distribution,
    DistributionList,
    QRCodeDistribution,
)

# Register your models here.

admin.site.register(Distribution)
admin.site.register(DistributionList)
admin.site.register(QRCodeDistribution)
