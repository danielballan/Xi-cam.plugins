def test_IFittableModelPlugin():
    from ..FittableModelPlugin import Fittable1DModelPlugin
    import numpy as np
    from astropy.modeling.fitting import LevMarLSQFitter
    from astropy.modeling import Parameter

    # Below example copied from AstroPy for demonstration; Gaussian1D is already a member of astropy's models
    class Gaussian1D(Fittable1DModelPlugin):
        amplitude = Parameter("amplitude")
        mean = Parameter("mean")
        stddev = Parameter("stddev")

        @staticmethod
        def evaluate(x, amplitude, mean, stddev):
            """
            Gaussian1D model function.
            """
            return amplitude * np.exp(- 0.5 * (x - mean) ** 2 / stddev ** 2)

        @staticmethod
        def fit_deriv(x, amplitude, mean, stddev):
            """
            Gaussian1D model function derivatives.
            """

            d_amplitude = np.exp(-0.5 / stddev ** 2 * (x - mean) ** 2)
            d_mean = amplitude * d_amplitude * (x - mean) / stddev ** 2
            d_stddev = amplitude * d_amplitude * (x - mean) ** 2 / stddev ** 3
            return [d_amplitude, d_mean, d_stddev]

    # Generate fake data
    np.random.seed(0)
    x = np.linspace(-5., 5., 200)
    m_ref = Gaussian1D(amplitude=2., mean=1, stddev=3)
    from astropy.modeling.models import Gaussian1D
    Gaussian1D()(x)
    y = m_ref(x) + np.random.normal(0., 0.1, x.shape)

    # Fit model to data
    m_init = Gaussian1D()

    fit = LevMarLSQFitter()
    m = fit(m_init, x, y)

    assert round(m.amplitude.value) == 2
    assert round(m.mean.value) == 1
    assert round(m.stddev.value) == 3


def test_IProcessingPlugin():
    from ..ProcessingPlugin import ProcessingPlugin, Input, Output

    class SumProcessingPlugin(ProcessingPlugin):
        a = Input(default=1, unit='nm', min=0)
        b = Input(default=2)
        c = Output()

        def evaluate(self):
            self.c.value = self.a.value + self.b.value
            return self.c.value

    t1 = SumProcessingPlugin()
    t2 = SumProcessingPlugin()
    assert t1.evaluate() == 3
    t1.a.value = 100
    assert t2.a.value == 1
    assert t1.inputs['a'].name == 'a'
    assert t1.outputs['c'].name == 'c'
    assert t1.outputs['c'].value == 3


def makeapp():
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    return app


def mainloop():
    from qtpy.QtWidgets import QApplication
    app = QApplication.instance()
    app.exec_()


def test_IDataSourcePlugin():
    from ..DataResourcePlugin import DataResourcePlugin, DataSourceListModel

    class SpotDataResourcePlugin(DataResourcePlugin):
        def __init__(self, user='anonymous', password='',
                     query='skipnum=0&sortterm=fs.stage_date&sorttype=desc&search=end_station=bl832'):
            scheme = 'https'
            host = 'portal-auth.nersc.gov'
            path = 'als/hdf/search'
            config = {'scheme': scheme, 'host': host, 'path': path, 'query': query}
            super(SpotDataResourcePlugin, self).__init__(flags={'canPush': False}, **config)
            from requests import Session
            self.session = Session()
            self.session.post("https://newt.nersc.gov/newt/auth", {"username": user, "password": password})
            r = self.session.get(
                'https://portal-auth.nersc.gov/als/hdf/search?skipnum=0&limitnum=10&sortterm=fs.stage_date&sorttype=desc&search=end_station=bl832')
            self._data = eval(r.content.replace(b'false', b'False'))

        def columnCount(self, index=None):
            return len(self._data[0])

        def rowCount(self, index=None):
            return len(self._data)

        def data(self, index, role):
            from qtpy.QtCore import Qt, QVariant
            if index.isValid() and role == Qt.DisplayRole:
                return QVariant(self._data[index.row()]['name'])
            else:
                return QVariant()

                # TODO: remove qtcore dependence

    app = makeapp()
    from qtpy.QtWidgets import QListView

    # TODO: handle password for testing
    spot = DataSourceListModel(SpotDataResourcePlugin())

    lv = QListView()
    lv.setModel(spot)
    lv.show()
    mainloop()