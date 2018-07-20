from os import path
import tkinter as tk
from tkinter import scrolledtext
import functools
from tkinter import filedialog
from tkinter.ttk import Combobox
from enum import Enum
from ntpath import basename
import re
import csv
import plotly
import plotly.graph_objs as go
import datetime
from collections import OrderedDict

class FuelType(Enum):
    electricity = 1
    gas = 2

class EnergyMonitor():

    def __init__(self, parent):
        self.parent = parent

        self.data_container = OrderedDict()
        self.monthly_data = OrderedDict()
        self.loaded_ids = []
        self.loaded_fuels = []

        self.welcome_label = tk.Label(self.parent, text='Welcome to the Energy Monitor!', font=('Calibri', 32))
        self.welcome_label.configure(background='#c6e2ff')
        self.welcome_label.pack()

        self.message_label = tk.Label(self.parent, text='Please use the dialog below to load a CSV file, which will be displayed ' +
                                          'in the box below.', font=('Calibri', 14), wraplength=540)
        self.message_label.configure(background='#c6e2ff')
        self.message_label.pack(pady=20)

        # self.btn_file = Button(parent, text="Load file", command=load_file)
        self.btn_file = tk.Button(self.parent, text="Load file", command=self.load_file)
        self.btn_file.pack(pady=20)

        self.scrolled_text = tk.scrolledtext.ScrolledText(self.parent, width=40, height=10)
        self.scrolled_text.pack()

        self.house_combo = Combobox(self.parent)
        self.house_combo.pack_forget()

        self.fuel_label = tk.Label(self.parent, text="", font=('Calibri', 11))
        self.fuel_label.pack_forget()

        self.btn_graph_annual = tk.Button(self.parent, text='Annual Usage', command=
            functools.partial(self.generate_annual_graph_singlehouse, self.house_combo.get()))
        self.btn_graph_annual.pack_forget()

        self.btn_graph_monthly = tk.Button(self.parent, text='Monthly Usage', command=
            functools.partial(self.generate_monthly_graph_singlehouse, self.house_combo.get()))
        self.btn_graph_monthly.pack_forget()

        self.btn_graph_multiple_monthly = tk.Button(self.parent, text='All Houses Monthly Usage', command=
            functools.partial(self.generate_graph_monthly_multiple, self.house_combo.get()))
        self.btn_graph_multiple_monthly.pack_forget()

        self.selected_radio = tk.IntVar()
        self.radio_gas = tk.Radiobutton(self.parent, text="Gas", value=FuelType.gas.value, variable=self.selected_radio)
        self.radio_electric = tk.Radiobutton(self.parent, text="Electricity", value=FuelType.electricity.value,
                                             variable=self.selected_radio)
        self.radio_gas.pack_forget()
        self.radio_electric.pack_forget()

    def load_file(self, file=None):

        if file is None:
            file = filedialog.askopenfilename(initialdir=path.dirname(__file__))
        elif not path.isfile(file):
            raise ValueError("This file does not exist or is not readable.")

        print(file)

        re_single_house = re.compile('^(.*?)_both_daily$')
        re_multiple_houses = re.compile('^(gas|electricity)_daily$')

        filename = basename(file).split('.')[0]
        single_match = re_single_house.search(filename)
        multiple_match = re_multiple_houses.search(filename)

        if single_match is not None:
            self.process_single_file(file, single_match.group(1))
        elif multiple_match is not None:
            fuel_type = FuelType[multiple_match.group(1)]
            self.process_multiple_file(file, fuel_type)
        else:
            raise ValueError("File format is not correct, must be one of '{fuel-type}_daily.csv"
                              + " or '{house-id}_both_daily.csv is invalid")

        self.house_combo.configure(values=self.loaded_ids)
        self.house_combo.current(0)
        self.house_combo.pack(pady=5)

        self.fuel_label.configure(text="Available fuel types: " + ','.join(list(map(lambda f: str(f.name),
                                                                                    self.loaded_fuels))))
        self.fuel_label.pack(pady=20)

        self.btn_graph_annual.pack(pady=5)
        self.btn_graph_monthly.pack()

        if len(self.loaded_ids) > 1:

            self.btn_graph_multiple_monthly.pack()
            if FuelType.gas in self.loaded_fuels:
                self.radio_gas.pack()
            if FuelType.electricity in self.loaded_fuels:
                self.radio_electric.pack()




    def process_single_file(self, file, house_id):
        print("This file is a single house with both fuel types. The house id is '%s'." % house_id)
        print("Deleting old data")
        self.data_container.clear()
        self.loaded_ids.clear()
        self.loaded_fuels.clear()

        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

            if header[1].lower() != 'electricity' or header[2].lower() != 'gas':
                raise ValueError('File is not in correct format. First column must be electricity, second must be gas.')

            for row in reader:
                print(row)
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                self.data_container[this_date] = {house_id: {FuelType.electricity: float(row[1]),
                                                             FuelType.gas: float(row[2])}}

            # Since we have only loaded one file, set the id directly
            self.loaded_ids.append(house_id)
            self.loaded_fuels.extend([FuelType.electricity, FuelType.gas])


    def process_multiple_file(self, file, fuel_type):
        print("This file is a multiple house file with %s data." % fuel_type)

        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)
            # Add the loaded ids to the list
            self.loaded_ids = header[1:len(header)]


            if fuel_type not in self.loaded_fuels:
                self.loaded_fuels.append(fuel_type)

            if header[0].lower() != 'date':
                raise ValueError('The header line must begin with a date column, then a column for each property')

            for row in reader:
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                if this_date not in self.data_container:
                    self.data_container[this_date] = {}

                # Validate number of rows with data in is correct with the header
                if len(row) != len(header):
                    raise ValueError('The number of elements in this row is not correct.')

                for index in range(1, len(row)):

                    this_house_id = header[index]
                    if this_house_id not in self.data_container[this_date]:
                        self.data_container[this_date][this_house_id] = {}

                    self.data_container[this_date][this_house_id][fuel_type] = row[index]



    def generate_monthly_data(self):
        print('Generating monthly data')

        this_monthly_data = OrderedDict()

        for date in self.data_container:
            this_date = datetime.date(date.year, date.month, 1)

            if this_date not in this_monthly_data:
                this_monthly_data[this_date] = {}

            for house in self.data_container[this_date].keys():

                if house not in this_monthly_data[this_date]:
                    this_monthly_data[this_date][house] = {FuelType.gas: 0.0, FuelType.electricity: 0.0}

                if FuelType.gas in self.data_container[date][house]:
                    this_monthly_data[this_date][house][FuelType.gas] += float(self.data_container[date][house][FuelType.gas])

                if FuelType.electricity in self.data_container[date][house]:
                    this_monthly_data[this_date][house][FuelType.electricity] += float(
                        self.data_container[date][house][FuelType.electricity])

        return this_monthly_data


    def generate_metrics(self):
        print("Metrics")
    #     When the combobox changes we should fill the scroll bar with metrics for that house


    def generate_monthly_graph_singlehouse(self, house_id=None):

        if house_id is None:
            raise ValueError("No house ID passed in, cannot generate graph.")
        elif house_id == '':
            house_id = self.house_combo.get()

        print("Generating monthly data for house with id %s" % house_id)
        self.monthly_data = self.generate_monthly_data()

        date_range = list(self.monthly_data.keys())
        (gas_values, electricity_values) = ([], [])

        for date in date_range:

            if FuelType.gas not in self.monthly_data[date][house_id] \
                    or FuelType.electricity not in self.monthly_data[date][house_id]:

                raise KeyError("Both fuel values must be present to display this graph correctly.")

            gas_values.append(self.monthly_data[date][house_id][FuelType.gas])
            electricity_values.append(self.monthly_data[date][house_id][FuelType.electricity])

        gas_trace = go.Scatter(
            x=date_range,
            y=gas_values,
            name='Gas'
        )

        electricity_trace = go.Scatter(
            x=date_range,
            y=electricity_values,
            name='Electricity',
            yaxis='y2'
        )

        layout = go.Layout(
            title='Monthly Both Fuels',
            yaxis=dict(
                title='Gas Usage (kWh)'
            ),
            yaxis2=dict(
                title='Electricity Usage (kWh)',
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )
        fig = go.Figure(data=[gas_trace, electricity_trace],
                        layout=layout)
        plotly.offline.plot(fig, auto_open=True)


    def generate_graph(self):
        print("Stub method for generating graphs")


    # Use this one in the submitted code, keep the agnosting one separate
    def generate_annual_graph_singlehouse(self, house_id=None):

        if house_id is None:
            raise ValueError("No house ID passed in, cannot generate graph.")
        elif house_id == '':
            house_id = self.house_combo.get()

        date_range = list(self.data_container.keys())
        (gas_values, electricity_values) = ([], [])

        for date in date_range:

            if FuelType.gas not in self.data_container[date][house_id] \
                    or FuelType.electricity not in self.data_container[date][house_id]:

                raise KeyError("Both fuel values must be present to display this graph correctly.")

            gas_values.append(self.data_container[date][house_id][FuelType.gas])
            electricity_values.append(self.data_container[date][house_id][FuelType.electricity])

        gas_trace = go.Scatter(
            x=date_range,
            y=gas_values,
            name='gas trace'
        )

        electricity_trace = go.Scatter(
            x=date_range,
            y=electricity_values,
            name='electricity trace',
            yaxis='y2'
        )
        graph_data = [gas_trace, electricity_trace]

        layout = go.Layout(
            title='Single House Both Fuels',
            yaxis=dict(
                title='Usage (kWh)'
            ),
            yaxis2=dict(
                title='yaxis2 title',
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )

        fig = go.Figure(data=graph_data, layout=layout)
        plotly.offline.plot(fig, auto_open=True)


    def generate_graph_singlehouse(self, data, house_id=None):

        if house_id is None:
            raise ValueError("No house ID passed in, cannot generate graph.")
        elif house_id == '':
            house_id = self.house_combo.get()

        date_range = list(data.keys())
        (gas_values, electricity_values) = ([], [])

        for date in date_range:

            if FuelType.gas not in data[date][house_id] \
                    or FuelType.electricity not in data[date][house_id]:

                raise KeyError("Both fuel values must be present to display this graph correctly.")

            gas_values.append(data[date][house_id][FuelType.gas])
            electricity_values.append(data[date][house_id][FuelType.electricity])

        gas_trace = go.Scatter(
            x=date_range,
            y=gas_values,
            name='gas trace'
        )

        electricity_trace = go.Scatter(
            x=date_range,
            y=electricity_values,
            name='electricity trace',
            yaxis='y2'
        )
        graph_data = [gas_trace, electricity_trace]

        layout = go.Layout(
            title='Single House Both Fuels',
            yaxis=dict(
                title='Usage (kWh)'
            ),
            yaxis2=dict(
                title='yaxis2 title',
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )

        fig = go.Figure(data=graph_data, layout=layout)
        plotly.offline.plot(fig, auto_open=True)


    def generate_graph_monthly_multiple(self, fuel_type=None):

        if fuel_type is None or fuel_type == '':
            fuel_type = FuelType(self.selected_radio.get())

        self.monthly_data = self.generate_monthly_data()

        if fuel_type is None:
            # TODO fetch the value somehow
            fuel_type = FuelType.gas

        date_range = list(self.monthly_data.keys())
        usages = OrderedDict()
        data = []

        for date in date_range:
            for house in list(self.monthly_data[date].keys()):
                if house not in usages:
                    usages[house] = []

                usages[house].append(self.monthly_data[date][house][fuel_type])

        for house in list(usages.keys()):
            data.append(go.Bar(
                x=date_range,
                y=usages[house],
                name=house))

        layout = go.Layout(
            barmode='group'
        )

        fig = go.Figure(data=data, layout=layout)
        plotly.offline.plot(fig, auto_open=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Energy Monitor")
    root.geometry('600x750')
    root.configure(background='#c6e2ff')

    plotly.tools.set_credentials_file(username='josh.power', api_key='0R0G5rbmFrvqIqeTsHhG')
    print(plotly.__version__)

    gui = EnergyMonitor(root)
    root.mainloop()
