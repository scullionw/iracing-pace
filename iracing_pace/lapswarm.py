import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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


    def create_plot(self, title, violin=False):
        sns.set(style="whitegrid")

        if violin:
            ax = sns.violinplot(x="Driver", y="Lap Time", data=self.df)
        else:
            ax = sns.swarmplot(x="Driver", y="Lap Time", data=self.df)
        
        for item in ax.get_xticklabels():
            item.set_rotation(90)

        ax.set_title(title)
        
        return ax
        

def export_plot(ax, file_path):
    figure = ax.get_figure()    
    figure.savefig(file_path, bbox_inches='tight', dpi=400)

def interactive_plot(ax):
    plt.show()

   

    

    

    
