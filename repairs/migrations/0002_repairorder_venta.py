import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repairs', '0001_initial'),
        ('sales', '0002_sale_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='repairorder',
            name='venta',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orden_servicio',
                to='sales.sale',
                verbose_name='Venta asociada',
                help_text=(
                    'Venta generada automáticamente al facturar esta orden (ver '
                    'RepairOrder.facturar). Al ser OneToOne, su sola presencia '
                    'impide que la orden se facture dos veces.'
                ),
            ),
        ),
    ]
