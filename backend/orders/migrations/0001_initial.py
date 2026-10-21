import orders.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(default=orders.models.generate_order_id, editable=False, max_length=16, unique=True)),
                ('customer_name', models.CharField(max_length=120)),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('status', models.CharField(choices=[('placed', 'Placed'), ('baking', 'Baking'), ('ready', 'Ready for pickup'), ('done', 'Picked up')], db_index=True, default='placed', max_length=12)),
                ('payment', models.CharField(choices=[('cash', 'Cash on pickup'), ('paid', 'Paid online')], default='cash', max_length=12)),
                ('pickup_at', models.DateTimeField(db_index=True)),
                ('placed_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ready_at', models.DateTimeField(blank=True, null=True)),
                ('notification_email', models.EmailField(blank=True, max_length=254)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=9)),
                ('tax', models.DecimalField(decimal_places=2, max_digits=9)),
                ('total', models.DecimalField(decimal_places=2, max_digits=9)),
            ],
            options={'ordering': ('pickup_at', 'placed_at')},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=120)),
                ('detail', models.CharField(max_length=160)),
                ('quantity', models.PositiveSmallIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('note', models.CharField(blank=True, max_length=240)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
            ],
        ),
    ]
