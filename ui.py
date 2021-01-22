import threading
import ipywidgets as ipw
import pandas as pd
import bqplot as bq
import time


class Plot(bq.Figure):
    subseayellow = "#f8ed9b"
    subseagreen = "#00a0b0"
    subseapink = "#f3776f"
    subseablue = "#012b5d"
    subseagreydark = "#c0c1ba"
    colors = [subseablue, subseapink, subseagreen, subseayellow, subseagreydark]

    def __init__(self, timedeltafunction, datafunction, grid_area, live=True, title="", ylabel=""):
        """Plotter class

        Parameters
        ----------
        timedeltafunction : callable
            should return pandas.Timedelta
        datafunction : callable
            should return [{"s":pandas.Series, "labels":["label"]}, ...]
        grid_area : str
            name in css grid
        """
        self.timedeltafunction = timedeltafunction
        self.datafunction = datafunction
        self.live = live

        self.scales = self.get_scales()
        self.axx, self.axy = self.get_axes(ylabel=ylabel)
        self.marks = self.get_marks()
        margin = 30
        super().__init__(
            marks=self.marks,
            title=title,
            axes=[self.axx, self.axy],
            legend_style={"fill": "white"},
            legend_location="bottom-left",
            animation_duration=700,
            legend_text={"font-size": 16},
            fig_margin={
                "top": margin + 5,
                "bottom": margin - 5,
                "left": margin + 30,
                "right": margin,
            },
        )
        self.layout = ipw.Layout(grid_area=grid_area, width="auto", height="auto")
        self.start()

    def update_loop(self):
        while self.live:
            time.sleep(1)
            self.redraw()

    def start(self):
        self.live = True
        thread = threading.Thread(target=self.update_loop)
        thread.start()

    def stop(self):
        self.live = False

    def get_scales(self):
        return {"x": bq.DateScale(), "y": bq.LinearScale()}

    @staticmethod
    def get_axes_limits(lower, upper):
        diff = upper - lower
        _min = lower - diff * 0.3
        _max = upper + diff * 0.1
        return _min, _max

    def redraw(self):
        margin = pd.Timedelta('30s')
        data = self.datafunction()
        end = pd.Timestamp.now()
        start = end - self.timedeltafunction()
        maxs = []
        mins = []
        for d, mark in zip(data, self.marks):
            if len(d["s"]) > 0:
                array = d["s"][start-margin:end+margin]
                x = array.index
                y = array.values
                mark.x = x
                mark.y = y
                maxs.append(max(y))
                mins.append(min(y))
        y_limits = self.get_axes_limits(min(mins), max(maxs))
        self.scales["x"].min = start
        self.scales["x"].max = end
        self.scales["y"].min = y_limits[0]
        self.scales["y"].max = y_limits[1]

    def get_marks(self):
        marks = []
        data = self.datafunction()
        for d, c in zip(data, self.colors):
            marks.append(
                bq.Lines(
                    x=[],
                    y=[],
                    icon="line-chart",
                    scales=self.scales,
                    stroke_width=2,
                    fill='bottom',
                    fill_opacities=[0.2],
                    colors=[c],
                    labels=d["labels"],
                    display_legend=True,
                )
            )
        return marks

    def get_axes(self, ylabel):
        font_size = 15
        axx = bq.Axis(
            scale=self.scales["x"],
            grid_lines="solid",
            tick_format="%H:%M:%S",
            tick_style={"font-size": font_size},
        )
        axy = bq.Axis(
            scale=self.scales["y"],
            grid_lines="solid",
            orientation="vertical",
            label=ylabel,
            label_offset="40px",
            tick_style={"font-size": font_size},
        )
        return axx, axy


class UI(ipw.GridBox):
    def __init__(self, timedeltafunction, datafunction):
        super().__init__()
        self.live = True

        self.toggle_button = ipw.Button(
            description="Pause",
            button_style="success",
            tooltip="Press to toggle live update",
            layout=ipw.Layout(
                grid_area="toggle", width="100px", margin="9px 0px 0px 0px"
            ),
        )
        self.toggle_button.on_click(self.toggle)

        self.plot = Plot(
            timedeltafunction, datafunction, 'plot'
        )

        self.children = [
            self.toggle_button,
            self.plot,
        ]

        self.layout = ipw.Layout(
            width="100%",
            height="93vh",
            grid_template_rows="50px 500px",
            grid_template_columns="auto 900px auto",
            grid_template_areas="""
                ". toggle ."
                ". plot ."
                """,
        )

    def toggle(self, *args):
        if self.live:
            self.plot.stop()
            self.live = False
            self.toggle_button.description = "Start"
        elif not self.live:
            self.plot.start()
            self.live = True
            self.toggle_button.description = "Pause"
