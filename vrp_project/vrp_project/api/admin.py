from django.contrib import admin
from api.models import Vehicle, Address, Customer, Batch, Solution

# registering the implemented models in admin application
admin.site.register(Vehicle)
admin.site.register(Address)
admin.site.register(Customer)
admin.site.register(Batch)
admin.site.register(Solution)
