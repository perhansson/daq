
class EpixPlot:
    """ Hold matplotlib axes"""
    def __init__(self, name, axes):
        self.name = name
        self.axes = axes
        self.img = None
    def __eq__(self,other):
        return self.name == other.name
    def __ne__(self,other):
        return self.__eq__(other)
    
class EpixPlots:
    """ Hold matplotlib axes"""
    def __init__(self):
        self.plots = []

    def add_plot(self, epixPlot):
        self.plots.append(epixPlot)

    def get_plot(self, name):
        for ep in self.plots:
            if ep.name == name:
                return ep
        return None
