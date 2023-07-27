import random

import pytest

from geomstats.geometry.general_linear import GeneralLinear, SquareMatrices
from geomstats.test.parametrizers import DataBasedParametrizer
from geomstats.test_cases.geometry.general_linear import GeneralLinearTestCase
from geomstats.test_cases.geometry.lie_algebra import MatrixLieAlgebraTestCase
from geomstats.test_cases.geometry.riemannian_metric import RiemannianMetricTestCase

from .data.general_linear import (
    GeneralLinear2TestData,
    GeneralLinear3TestData,
    GeneralLinearMatricesMetricTestData,
    GeneralLinearTestData,
    SquareMatrices3TestData,
)
from .data.lie_algebra import MatrixLieAlgebraTestData


@pytest.fixture(
    scope="class",
    params=[
        (2, True),
        (2, False),
        (random.randint(3, 5), True),
        (random.randint(3, 5), False),
    ],
)
def spaces(request):
    n, positive_det = request.param
    request.cls.space = GeneralLinear(n=n, positive_det=positive_det, equip=False)


@pytest.mark.usefixtures("spaces")
class TestGeneralLinear(GeneralLinearTestCase, metaclass=DataBasedParametrizer):
    testing_data = GeneralLinearTestData()


@pytest.mark.smoke
class TestGeneralLinear2(GeneralLinearTestCase, metaclass=DataBasedParametrizer):
    space = GeneralLinear(n=3)
    testing_data = GeneralLinear2TestData()


@pytest.mark.smoke
class TestGeneralLinear3(GeneralLinearTestCase, metaclass=DataBasedParametrizer):
    space = GeneralLinear(n=3)
    testing_data = GeneralLinear3TestData()


@pytest.fixture(
    scope="class",
    params=[
        (random.randint(2, 5), True),
        (random.randint(2, 5), False),
    ],
)
def equipped_spaces(request):
    n, positive_det = request.param
    request.cls.space = GeneralLinear(n=n, positive_det=positive_det, equip=True)


@pytest.mark.usefixtures("equipped_spaces")
class TestMatricesMetric(RiemannianMetricTestCase, metaclass=DataBasedParametrizer):
    testing_data = GeneralLinearMatricesMetricTestData()


@pytest.fixture(
    scope="class",
    params=[
        2,
        random.randint(3, 5),
    ],
)
def square_matrices_spaces(request):
    request.cls.space = SquareMatrices(n=request.param)


@pytest.mark.usefixtures("square_matrices_spaces")
class TestSquareMatrices(MatrixLieAlgebraTestCase, metaclass=DataBasedParametrizer):
    testing_data = MatrixLieAlgebraTestData()


@pytest.mark.smoke
class TestSquareMatrices3(MatrixLieAlgebraTestCase, metaclass=DataBasedParametrizer):
    space = SquareMatrices(n=3)
    testing_data = SquareMatrices3TestData()
