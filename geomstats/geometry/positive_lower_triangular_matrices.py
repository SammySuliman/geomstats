"""The manifold of lower triangular matrices with positive diagonal elements.

Lead authors: Olivier Bisson and Saiteja Utpala.

References
----------
.. [T2022] Yann Thanwerdas. Riemannian and stratified
    geometries on covariance and correlation matrices. Differential
    Geometry [math.DG]. Université Côte d'Azur, 2022.
"""

import geomstats.backend as gs
from geomstats.geometry.base import DiffeomorphicManifold, VectorSpaceOpenSet
from geomstats.geometry.diffeo import Diffeo
from geomstats.geometry.invariant_metric import _InvariantMetricMatrix
from geomstats.geometry.lie_group import MatrixLieGroup
from geomstats.geometry.lower_triangular_matrices import LowerTriangularMatrices
from geomstats.geometry.matrices import Matrices
from geomstats.geometry.open_hemisphere import OpenHemisphere, OpenHemispheresProduct
from geomstats.geometry.pullback_metric import PullbackDiffeoMetric
from geomstats.geometry.riemannian_metric import RiemannianMetric


class PositiveLowerTriangularMatrices(MatrixLieGroup, VectorSpaceOpenSet):
    """Manifold of lower triangular matrices with >0 diagonal.

    This manifold is also called the cholesky space.

    Parameters
    ----------
    n : int
        Integer representing the shape of the matrices: n x n.

    References
    ----------
    .. [TP2019] Z Lin. "Riemannian Geometry of Symmetric
        Positive Definite Matrices Via Cholesky Decomposition"
        SIAM journal on Matrix Analysis and Applications , 2019.
        https://arxiv.org/abs/1908.09326
    """

    def __init__(self, n, equip=True):
        super().__init__(
            representation_dim=n,
            lie_algebra=LowerTriangularMatrices(n, equip=False),
            dim=int(n * (n + 1) / 2),
            embedding_space=LowerTriangularMatrices(n, equip=False),
            equip=equip,
        )
        self.n = n

    @staticmethod
    def default_metric():
        """Metric to equip the space with if equip is True."""
        return CholeskyMetric

    def random_point(self, n_samples=1, bound=1.0):
        """Sample in PLT.

        Parameters
        ----------
        n_samples : int
            Number of samples.
            Optional, default: 1.
        bound : float
            Side of hypercube support of the uniform distribution.
            Optional, default: 1.0

        Returns
        -------
        point : array-like, shape=[..., *point_shape]
           Sample.
        """
        batch_shape = (n_samples,) if n_samples > 1 else ()
        shape = batch_shape + (self.dim - self.n,)

        lower_part = bound * (gs.random.rand(*shape) - 0.5) * 2

        diag_shape = batch_shape + (self.n,)
        diagonal = bound * gs.random.rand(*diag_shape) + gs.atol

        return gs.mat_from_diag_triu_tril(diagonal, gs.array([0.0]), lower_part)

    def belongs(self, point, atol=gs.atol):
        """Check if mat is lower triangular with >0 diagonal.

        Parameters
        ----------
        point : array-like, shape=[..., n, n]
            Matrix to be checked.
        atol : float
            Tolerance.
            Optional, default: backend atol.

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean denoting if mat belongs to cholesky space.
        """
        is_lower_triangular = self.embedding_space.belongs(point, atol)
        diagonal = Matrices.diagonal(point)
        is_positive = gs.all(diagonal > 0, axis=-1)
        return gs.logical_and(is_lower_triangular, is_positive)

    def projection(self, point):
        """Project a matrix to the PLT space.

        Parameters
        ----------
        point : array-like, shape=[..., n, n]

        Returns
        -------
        projected: array-like, shape=[..., n, n]
        """
        vec_diag = gs.abs(Matrices.diagonal(point))
        vec_diag = gs.where(vec_diag < gs.atol, gs.atol, vec_diag)
        diag = gs.vec_to_diag(vec_diag)
        strictly_lower_triangular = gs.tril(point, k=-1)
        return diag + strictly_lower_triangular


class CholeskyMetric(RiemannianMetric):
    """Class for Cholesky metric on Cholesky space.

    References
    ----------
    .. [TP2019] . "Riemannian Geometry of Symmetric
        Positive Definite Matrices Via Cholesky Decomposition"
        SIAM journal on Matrix Analysis and Applications , 2019.
        https://arxiv.org/abs/1908.09326
    """

    @staticmethod
    def diag_inner_product(tangent_vec_a, tangent_vec_b, base_point):
        """Compute the inner product using only diagonal elements.

        Parameters
        ----------
        tangent_vec_a : array-like, shape=[..., n, n]
            Tangent vector at base point.
        tangent_vec_b : array-like, shape=[..., n, n]
            Tangent vector at base point.
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        ip_diagonal : array-like, shape=[...]
            Inner-product.
        """
        inv_sqrt_diagonal = gs.power(Matrices.diagonal(base_point), -2)
        tangent_vec_a_diagonal = Matrices.diagonal(tangent_vec_a)
        tangent_vec_b_diagonal = Matrices.diagonal(tangent_vec_b)
        prod = tangent_vec_a_diagonal * tangent_vec_b_diagonal * inv_sqrt_diagonal
        return gs.sum(prod, axis=-1)

    @staticmethod
    def strictly_lower_inner_product(tangent_vec_a, tangent_vec_b):
        """Compute the inner product using only strictly lower triangular elements.

        Parameters
        ----------
        tangent_vec_a : array-like, shape=[..., n, n]
            Tangent vector at base point.
        tangent_vec_b : array-like, shape=[..., n, n]
            Tangent vector at base point.

        Returns
        -------
        ip_sl : array-like, shape=[...]
            Inner-product.
        """
        sl_tagnet_vec_a = gs.tril_to_vec(tangent_vec_a, k=-1)
        sl_tagnet_vec_b = gs.tril_to_vec(tangent_vec_b, k=-1)
        ip_sl = gs.dot(sl_tagnet_vec_a, sl_tagnet_vec_b)
        return ip_sl

    @classmethod
    def inner_product(cls, tangent_vec_a, tangent_vec_b, base_point):
        """Compute the inner product.

        Compute the inner-product of tangent_vec_a and tangent_vec_b
        at point base_point using the cholesky Riemannian metric.

        Parameters
        ----------
        tangent_vec_a : array-like, shape=[..., n, n]
            Tangent vector at base point.
        tangent_vec_b : array-like, shape=[..., n, n]
            Tangent vector at base point.
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        inner_product : array-like, shape=[...]
            Inner-product.
        """
        diag_inner_product = cls.diag_inner_product(
            tangent_vec_a, tangent_vec_b, base_point
        )
        strictly_lower_inner_product = cls.strictly_lower_inner_product(
            tangent_vec_a, tangent_vec_b
        )
        return diag_inner_product + strictly_lower_inner_product

    def exp(self, tangent_vec, base_point, **kwargs):
        """Compute the Cholesky exponential map.

        Compute the Riemannian exponential at point base_point
        of tangent vector tangent_vec wrt the Cholesky metric.
        This gives a lower triangular matrix with positive elements.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., n, n]
            Tangent vector at base point.
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        exp : array-like, shape=[..., n, n]
            Riemannian exponential.
        """
        sl_base_point = Matrices.to_strictly_lower_triangular(base_point)
        sl_tangent_vec = Matrices.to_strictly_lower_triangular(tangent_vec)
        diag_base_point = Matrices.diagonal(base_point)
        diag_tangent_vec = Matrices.diagonal(tangent_vec)
        diag_product_expm = gs.exp(gs.divide(diag_tangent_vec, diag_base_point))

        sl_exp = sl_base_point + sl_tangent_vec
        diag_exp = gs.vec_to_diag(diag_base_point * diag_product_expm)
        return sl_exp + diag_exp

    def log(self, point, base_point, **kwargs):
        """Compute the Cholesky logarithm map.

        Compute the Riemannian logarithm at point base_point,
        of point wrt the Cholesky metric.
        This gives a tangent vector at point base_point.

        Parameters
        ----------
        point : array-like, shape=[..., n, n]
            Point.
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        log : array-like, shape=[..., n, n]
            Riemannian logarithm.
        """
        sl_base_point = Matrices.to_strictly_lower_triangular(base_point)
        sl_point = Matrices.to_strictly_lower_triangular(point)
        diag_base_point = Matrices.diagonal(base_point)
        diag_point = Matrices.diagonal(point)
        diag_product_logm = gs.log(gs.divide(diag_point, diag_base_point))

        sl_log = sl_point - sl_base_point
        diag_log = gs.vec_to_diag(diag_base_point * diag_product_logm)
        return sl_log + diag_log

    def squared_dist(self, point_a, point_b, **kwargs):
        """Compute the Cholesky Metric squared distance.

        Compute the Riemannian squared distance between point_a and point_b.

        Parameters
        ----------
        point_a : array-like, shape=[..., n, n]
            Point.
        point_b : array-like, shape=[..., n, n]
            Point.

        Returns
        -------
        _ : array-like, shape=[...]
            Riemannian squared distance.
        """
        log_diag_a = gs.log(Matrices.diagonal(point_a))
        log_diag_b = gs.log(Matrices.diagonal(point_b))
        diag_diff = log_diag_a - log_diag_b
        squared_dist_diag = gs.sum((diag_diff) ** 2, axis=-1)

        sl_a = Matrices.to_strictly_lower_triangular(point_a)
        sl_b = Matrices.to_strictly_lower_triangular(point_b)
        sl_diff = sl_a - sl_b
        squared_dist_sl = Matrices.frobenius_product(sl_diff, sl_diff)
        return squared_dist_sl + squared_dist_diag


class InvariantPositiveLowerTriangularMatricesMetric(_InvariantMetricMatrix):
    """Invariant metric on the positive lower triangular matrices."""

    def inner_product_at_identity(self, tangent_vec_a, tangent_vec_b):
        """Compute inner product at tangent space at identity.

        Parameters
        ----------
        tangent_vec_a : array-like, shape=[..., n, n]
            First tangent vector at identity.
        tangent_vec_b : array-like, shape=[..., n, n]
            Second tangent vector at identity.

        Returns
        -------
        inner_prod : array-like, shape=[...]
            Inner-product of the two tangent vectors.
        """
        if Matrices.is_diagonal(self.metric_mat_at_identity):
            return super().inner_product_at_identity(tangent_vec_a, tangent_vec_b)

        return gs.dot(
            gs.tril_to_vec(tangent_vec_a),
            gs.matvec(self.metric_mat_at_identity, gs.tril_to_vec(tangent_vec_b)),
        )


class UnitNormedRowsPLTDiffeo(Diffeo):
    """A diffeomorphism from UnitNormedRowsPLTDMatrices to OpenHemispheresProduct.

    A diffeomorphism between the space of lower triangular matrices with
    positive diagonal and unit normed rows and the product space of
    successively increasing factor-dimension open hemispheres.

    Given the way `OpenHemisphere` is implemented, i.e. the first component
    is positive, rows need to be flipped.
    """

    def __init__(self, n):
        super().__init__()
        self.n = n

    def diffeomorphism(self, base_point):
        """Diffeomorphism at base point.

        Parameters
        ----------
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        image_point : array-like, shape=[..., space_dim]
            Image point.
        """
        return gs.concatenate(
            [gs.flip(base_point[..., i, : i + 1], axis=-1) for i in range(1, self.n)],
            axis=-1,
        )

    def _from_product_to_mat(self, vec, ones=True):
        r"""Transform vector into matrix.

        A generalization of inverse diffeomorphism and inverse tangent
        diffeomorphism, where we can choose if the first element is one
        (diffeomorphism) or zero (tangent diffeormorphism).

        Parameters
        ----------
        vec : array-like, shape=[..., space_dim]

        Returns
        -------
        mat : array-like, shape=[..., n, n]
        """
        n = self.n
        flipped_vec = gs.flip(vec, axis=-1)
        batch_shape = vec.shape[:-1]

        gen_first = gs.ones if ones else gs.zeros

        first = gen_first(batch_shape + (1,))

        flipped_vec_ = gs.concatenate([flipped_vec, first], axis=-1)

        indices = sorted(zip(*gs.tril_indices(n)), key=lambda x: x[0], reverse=True)

        for n_batch in reversed(batch_shape):
            indices = [(k,) + indices_ for k in range(n_batch) for indices_ in indices]

        return gs.array_from_sparse(
            indices, gs.flatten(flipped_vec_), batch_shape + (n, n)
        )

    def inverse_diffeomorphism(self, image_point):
        r"""Inverse diffeomorphism at base point.

        :math:`f^{-1}: N \rightarrow M`

        Parameters
        ----------
        image_point : array-like, shape=[..., space_dim]
            Image point.

        Returns
        -------
        base_point : array-like, shape=[..., n, n]
            Base point.
        """
        return self._from_product_to_mat(image_point)

    def tangent_diffeomorphism(self, tangent_vec, base_point=None, image_point=None):
        r"""Tangent diffeomorphism at base point.

        df_p is a linear map from T_pM to T_f(p)N.
        The diffeomorphism is linear, so its pushforward is itself

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., n, n]
            Tangent vector at base point.
        base_point : array-like, shape=[..., n, n]
            Base point.
        image_point : array-like, shape=[..., space_dim]
            Image point.

        Returns
        -------
        image_tangent_vec : array-like, shape=[..., space_dim]
            Image tangent vector at image of the base point.
        """
        return self.diffeomorphism(tangent_vec)

    def inverse_tangent_diffeomorphism(
        self, image_tangent_vec, image_point=None, base_point=None
    ):
        r"""Inverse tangent diffeomorphism at image point.

        df^-1_p is a linear map from T_f(p)N to T_pM

        Parameters
        ----------
        image_tangent_vec : array-like, shape=[..., space_dim]
            Image tangent vector at image point.
        image_point : array-like, shape=[..., space_dim]
            Image point.
        base_point : array-like, shape=[..., n, n]
            Base point.

        Returns
        -------
        tangent_vec : array-like, shape=[..., *]
            Tangent vector at base point.
        """
        return self._from_product_to_mat(image_tangent_vec, ones=False)


class UnitNormedRowsPLTMatrices(DiffeomorphicManifold):
    """Space of positive lower triangular matrices with unit-normed rows.

    Rows are unit normed wrt Euclidean norm.

    For more details, check section 7.4.1 of [T2022]_.
    """

    def __init__(self, n, equip=True):
        diffeo = UnitNormedRowsPLTDiffeo(n=n)

        image_space = OpenHemispheresProduct(n=n) if n > 2 else OpenHemisphere(dim=1)

        super().__init__(
            dim=int(n * (n + 1) / 2),
            shape=(n, n),
            diffeo=diffeo,
            image_space=image_space,
            equip=equip,
        )
        self.n = n
        self.embedding_space = PositiveLowerTriangularMatrices(n=n, equip=False)

    @staticmethod
    def default_metric():
        """Metric to equip the space with if equip is True."""
        return UnitNormedRowsPLTMatricesPullbackMetric

    def belongs(self, point, atol=gs.atol):
        """Check if a point belongs to the unit normed plt matrices."""
        is_plt = self.embedding_space.belongs(point)
        is_unit_normed = self.image_space.belongs(
            self.diffeo.diffeomorphism(point),
        )
        return gs.logical_and(is_plt, is_unit_normed)

    def is_tangent(self, vector, base_point, atol=gs.atol):
        """Check whether the vector is tangent at base_point.

        Parameters
        ----------
        vector: array-like, shape = [..., *point_shape]
            Vector.
        base_point: array-like, shape = [..., *point_shape]
            Point on the manifold.
        atol: float
            Absolute tolerance.
            Optional, default: backend atol.

        Returns
        -------
        is_tangent: bool
            Boolean denoting if vector is a tangent vector at the base point.
        """
        is_lt = self.embedding_space.is_tangent(vector, base_point)
        first_is_zero = gs.isclose(vector[..., 0, 0], 0.0)

        image_point = self.diffeo.diffeomorphism(base_point)
        image_vector = self.diffeo.tangent_diffeomorphism(
            vector, base_point=base_point, image_point=image_point
        )
        image_is_tangent = self.image_space.is_tangent(
            image_vector, image_point, atol=atol
        )

        return gs.logical_and(
            gs.logical_and(is_lt, first_is_zero),
            image_is_tangent,
        )


class UnitNormedRowsPLTMatricesPullbackMetric(PullbackDiffeoMetric):
    """Pullback diffeo metric on `UnitNormedRowsPLTMatrices`.

    Results from the pullback of a metric on the `OpenHemispheresProduct`.
    """

    def __init__(self, space):
        super().__init__(
            space=space, diffeo=space.diffeo, image_space=space.image_space
        )
