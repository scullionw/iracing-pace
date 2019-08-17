import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator, FuncFormatter)
import pendulum

class EmptyResults(Exception):
    pass

class LapSwarm:
    
    def __init__(self, results, maxpos, maxdelta):
        self.grid, self.all_lap_times = results

        if len(self.grid) == 0 or len(self.all_lap_times) == 0:
            raise EmptyResults

        fastest_time = min(self.all_lap_times)
        dataset = []
        for name, info in self.grid.items():
            if int(info['pos']) <= maxpos:
                for lap in info['laps']:
                    if lap < fastest_time + maxdelta:
                        dataset.append({'Driver': f"{name}", 'Lap Time': lap})

        self.df = pd.DataFrame(dataset)


    def create_plot(self, title, violin=False, y_delta=None):
        plt.figure()
        sns.set(style="whitegrid")
        
        if violin:
            ax = sns.violinplot(x="Driver", y="Lap Time", data=self.df)
        else:
            ax = sns.swarmplot(x="Driver", y="Lap Time", data=self.df)
        
        for item in ax.get_xticklabels():
            item.set_rotation(90)

        if y_delta is not None:
            # ax.set_ylim([None,y_max])
            x1, x2, y1, _ = plt.axis()
            ax.axis((x1, x2, y1, y1 + y_delta))

        ax.yaxis.set_major_locator(MultipleLocator(.5))

        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: format_laptime(y))) 
        ax.set_title(title)
        
        return ax
        
def format_laptime(t):
    it = pendulum.duration(seconds=t)
    minutes = it.minutes
    seconds = it.remaining_seconds
    milliseconds = it.microseconds // 1000
    return f"{minutes}:{seconds:02}.{milliseconds:03}"


def export_plot(ax, file_path):
    figure = ax.get_figure()    
    figure.savefig(file_path, bbox_inches='tight', dpi=400)
    plt.clf()
    plt.cla()
    plt.close()

def interactive_plot(ax):
    plt.show()
    

   

    

    

    
