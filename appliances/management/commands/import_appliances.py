import csv
from pprint import pprint

import djclick as click
from appliances.models import Appliance, ProductLine


@click.command()
@click.argument("csv_file", type=click.File("r"))
def command(csv_file):
    csv_reader = csv.reader(csv_file)

    appliances = [
        Appliance(
            product_line=ProductLine.objects.get_or_create(name=product_line)[0],
            serial_number=serial_number,
            model_number=model_number,
        )
        for product_line, model_number, serial_number in csv_reader
    ]

    print("Here are the appliances extracted:")
    pprint(appliances)

    if click.confirm("Proceed?"):
        Appliance.objects.bulk_create(appliances)
