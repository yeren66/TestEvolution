a = """/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.commons.math4.legacy.analysis.interpolation;

import java.util.Arrays;
import java.util.function.DoubleBinaryOperator;
import java.util.function.Function;

import org.apache.commons.numbers.core.Sum;
import org.apache.commons.math4.legacy.analysis.BivariateFunction;
import org.apache.commons.math4.legacy.exception.DimensionMismatchException;
import org.apache.commons.math4.legacy.exception.NoDataException;
import org.apache.commons.math4.legacy.exception.NonMonotonicSequenceException;
import org.apache.commons.math4.legacy.exception.OutOfRangeException;
import org.apache.commons.math4.legacy.core.MathArrays;

/**
 * Function that implements the
 * <a href="http://en.wikipedia.org/wiki/Bicubic_interpolation">
 * bicubic spline interpolation</a>.
 *
 * @since 3.4
 */
public class BicubicInterpolatingFunction
    implements BivariateFunction {
    /** Number of coefficients. */
    private static final int NUM_COEFF = 16;
    /**
     * Matrix to compute the spline coefficients from the function values
     * and function derivatives values.
     */
    private static final double[][] AINV = {
        { 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 },
        { 0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0 },
        { -3,3,0,0,-2,-1,0,0,0,0,0,0,0,0,0,0 },
        { 2,-2,0,0,1,1,0,0,0,0,0,0,0,0,0,0 },
        { 0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0 },
        { 0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0 },
        { 0,0,0,0,0,0,0,0,-3,3,0,0,-2,-1,0,0 },
        { 0,0,0,0,0,0,0,0,2,-2,0,0,1,1,0,0 },
        { -3,0,3,0,0,0,0,0,-2,0,-1,0,0,0,0,0 },
        { 0,0,0,0,-3,0,3,0,0,0,0,0,-2,0,-1,0 },
        { 9,-9,-9,9,6,3,-6,-3,6,-6,3,-3,4,2,2,1 },
        { -6,6,6,-6,-3,-3,3,3,-4,4,-2,2,-2,-2,-1,-1 },
        { 2,0,-2,0,0,0,0,0,1,0,1,0,0,0,0,0 },
        { 0,0,0,0,2,0,-2,0,0,0,0,0,1,0,1,0 },
        { -6,6,6,-6,-4,-2,4,2,-3,3,-3,3,-2,-1,-2,-1 },
        { 4,-4,-4,4,2,2,-2,-2,2,-2,2,-2,1,1,1,1 }
    };

    /** Samples x-coordinates. */
    private final double[] xval;
    /** Samples y-coordinates. */
    private final double[] yval;
    /** Set of cubic splines patching the whole data grid. */
    private final BicubicFunction[][] splines;

    /**
     * @param x Sample values of the x-coordinate, in increasing order.
     * @param y Sample values of the y-coordinate, in increasing order.
     * @param f Values of the function on every grid point.
     * @param dFdX Values of the partial derivative of function with respect
     * to x on every grid point.
     * @param dFdY Values of the partial derivative of function with respect
     * to y on every grid point.
     * @param d2FdXdY Values of the cross partial derivative of function on
     * every grid point.
     * @throws DimensionMismatchException if the various arrays do not contain
     * the expected number of elements.
     * @throws NonMonotonicSequenceException if {@code x} or {@code y} are
     * not strictly increasing.
     * @throws NoDataException if any of the arrays has zero length.
     */
    public BicubicInterpolatingFunction(double[] x,
                                        double[] y,
                                        double[][] f,
                                        double[][] dFdX,
                                        double[][] dFdY,
                                        double[][] d2FdXdY)
        throws DimensionMismatchException,
               NoDataException,
               NonMonotonicSequenceException {
        this(x, y, f, dFdX, dFdY, d2FdXdY, false);
    }

    /**
     * @param x Sample values of the x-coordinate, in increasing order.
     * @param y Sample values of the y-coordinate, in increasing order.
     * @param f Values of the function on every grid point.
     * @param dFdX Values of the partial derivative of function with respect
     * to x on every grid point.
     * @param dFdY Values of the partial derivative of function with respect
     * to y on every grid point.
     * @param d2FdXdY Values of the cross partial derivative of function on
     * every grid point.
     * @param initializeDerivatives Whether to initialize the internal data
     * needed for calling any of the methods that compute the partial derivatives
     * this function.
     * @throws DimensionMismatchException if the various arrays do not contain
     * the expected number of elements.
     * @throws NonMonotonicSequenceException if {@code x} or {@code y} are
     * not strictly increasing.
     * @throws NoDataException if any of the arrays has zero length.
     */
    public BicubicInterpolatingFunction(double[] x,
                                        double[] y,
                                        double[][] f,
                                        double[][] dFdX,
                                        double[][] dFdY,
                                        double[][] d2FdXdY,
                                        boolean initializeDerivatives)
        throws DimensionMismatchException,
               NoDataException,
               NonMonotonicSequenceException {
        final int xLen = x.length;
        final int yLen = y.length;

        if (xLen == 0 || yLen == 0 || f.length == 0 || f[0].length == 0) {
            throw new NoDataException();
        }
        if (xLen != f.length) {
            throw new DimensionMismatchException(xLen, f.length);
        }
        if (xLen != dFdX.length) {
            throw new DimensionMismatchException(xLen, dFdX.length);
        }
        if (xLen != dFdY.length) {
            throw new DimensionMismatchException(xLen, dFdY.length);
        }
        if (xLen != d2FdXdY.length) {
            throw new DimensionMismatchException(xLen, d2FdXdY.length);
        }

        MathArrays.checkOrder(x);
        MathArrays.checkOrder(y);

        xval = x.clone();
        yval = y.clone();

        final int lastI = xLen - 1;
        final int lastJ = yLen - 1;
        splines = new BicubicFunction[lastI][lastJ];

        for (int i = 0; i < lastI; i++) {
            if (f[i].length != yLen) {
                throw new DimensionMismatchException(f[i].length, yLen);
            }
            if (dFdX[i].length != yLen) {
                throw new DimensionMismatchException(dFdX[i].length, yLen);
            }
            if (dFdY[i].length != yLen) {
                throw new DimensionMismatchException(dFdY[i].length, yLen);
            }
            if (d2FdXdY[i].length != yLen) {
                throw new DimensionMismatchException(d2FdXdY[i].length, yLen);
            }
            final int ip1 = i + 1;
            final double xR = xval[ip1] - xval[i];
            for (int j = 0; j < lastJ; j++) {
                final int jp1 = j + 1;
                final double yR = yval[jp1] - yval[j];
                final double xRyR = xR * yR;
                final double[] beta = new double[] {
                    f[i][j], f[ip1][j], f[i][jp1], f[ip1][jp1],
                    dFdX[i][j] * xR, dFdX[ip1][j] * xR, dFdX[i][jp1] * xR, dFdX[ip1][jp1] * xR,
                    dFdY[i][j] * yR, dFdY[ip1][j] * yR, dFdY[i][jp1] * yR, dFdY[ip1][jp1] * yR,
                    d2FdXdY[i][j] * xRyR, d2FdXdY[ip1][j] * xRyR, d2FdXdY[i][jp1] * xRyR, d2FdXdY[ip1][jp1] * xRyR
                };

                splines[i][j] = new BicubicFunction(computeSplineCoefficients(beta),
                                                    xR,
                                                    yR,
                                                    initializeDerivatives);
            }
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public double value(double x, double y)
        throws OutOfRangeException {
        final int i = searchIndex(x, xval);
        final int j = searchIndex(y, yval);

        final double xN = (x - xval[i]) / (xval[i + 1] - xval[i]);
        final double yN = (y - yval[j]) / (yval[j + 1] - yval[j]);

        return splines[i][j].value(xN, yN);
    }

    /**
     * Indicates whether a point is within the interpolation range.
     *
     * @param x First coordinate.
     * @param y Second coordinate.
     * @return {@code true} if (x, y) is a valid point.
     */
    public boolean isValidPoint(double x, double y) {
        return !(x < xval[0] ||
            x > xval[xval.length - 1] ||
            y < yval[0] ||
            y > yval[yval.length - 1]);
    }

    /**
     * @return the first partial derivative respect to x.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    public DoubleBinaryOperator partialDerivativeX() {
        return partialDerivative(BicubicFunction::partialDerivativeX);
    }

    /**
     * @return the first partial derivative respect to y.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    public DoubleBinaryOperator partialDerivativeY() {
        return partialDerivative(BicubicFunction::partialDerivativeY);
    }

    /**
     * @return the second partial derivative respect to x.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    public DoubleBinaryOperator partialDerivativeXX() {
        return partialDerivative(BicubicFunction::partialDerivativeXX);
    }

    /**
     * @return the second partial derivative respect to y.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    public DoubleBinaryOperator partialDerivativeYY() {
        return partialDerivative(BicubicFunction::partialDerivativeYY);
    }

    /**
     * @return the second partial cross derivative.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    public DoubleBinaryOperator partialDerivativeXY() {
        return partialDerivative(BicubicFunction::partialDerivativeXY);
    }

    /**
     * @param which derivative function to apply.
     * @return the selected partial derivative.
     * @throws NullPointerException if the internal data were not initialized
     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],
     *             double[][],double[][],double[][],boolean) constructor}).
     */
    private DoubleBinaryOperator partialDerivative(Function<BicubicFunction, BivariateFunction> which) {
        return (x, y) -> {
            final int i = searchIndex(x, xval);
            final int j = searchIndex(y, yval);

            final double xN = (x - xval[i]) / (xval[i + 1] - xval[i]);
            final double yN = (y - yval[j]) / (yval[j + 1] - yval[j]);

            return which.apply(splines[i][j]).value(xN, yN);
        };
    }

    /**
     * @param c Coordinate.
     * @param val Coordinate samples.
     * @return the index in {@code val} corresponding to the interval
     * containing {@code c}.
     * @throws OutOfRangeException if {@code c} is out of the
     * range defined by the boundary values of {@code val}.
     */
    private static int searchIndex(double c, double[] val) {
        final int r = Arrays.binarySearch(val, c);

        if (r == -1 ||
            r == -val.length - 1) {
            throw new OutOfRangeException(c, val[0], val[val.length - 1]);
        }

        if (r < 0) {
            // "c" in within an interpolation sub-interval: Return the
            // index of the sample at the lower end of the sub-interval.
            return -r - 2;
        }
        final int last = val.length - 1;
        if (r == last) {
            // "c" is the last sample of the range: Return the index
            // of the sample at the lower end of the last sub-interval.
            return last - 1;
        }

        // "c" is another sample point.
        return r;
    }

    /**
     * Compute the spline coefficients from the list of function values and
     * function partial derivatives values at the four corners of a grid
     * element. They must be specified in the following order:
     * <ul>
     *  <li>f(0,0)</li>
     *  <li>f(1,0)</li>
     *  <li>f(0,1)</li>
     *  <li>f(1,1)</li>
     *  <li>f<sub>x</sub>(0,0)</li>
     *  <li>f<sub>x</sub>(1,0)</li>
     *  <li>f<sub>x</sub>(0,1)</li>
     *  <li>f<sub>x</sub>(1,1)</li>
     *  <li>f<sub>y</sub>(0,0)</li>
     *  <li>f<sub>y</sub>(1,0)</li>
     *  <li>f<sub>y</sub>(0,1)</li>
     *  <li>f<sub>y</sub>(1,1)</li>
     *  <li>f<sub>xy</sub>(0,0)</li>
     *  <li>f<sub>xy</sub>(1,0)</li>
     *  <li>f<sub>xy</sub>(0,1)</li>
     *  <li>f<sub>xy</sub>(1,1)</li>
     * </ul>
     * where the subscripts indicate the partial derivative with respect to
     * the corresponding variable(s).
     *
     * @param beta List of function values and function partial derivatives
     * values.
     * @return the spline coefficients.
     */
    private static double[] computeSplineCoefficients(double[] beta) {
        final double[] a = new double[NUM_COEFF];

        for (int i = 0; i < NUM_COEFF; i++) {
            double result = 0;
            final double[] row = AINV[i];
            for (int j = 0; j < NUM_COEFF; j++) {
                result += row[j] * beta[j];
            }
            a[i] = result;
        }

        return a;
    }
}

/**
 * Bicubic function.
 */
class BicubicFunction implements BivariateFunction {
    /** Number of points. */
    private static final short N = 4;
    /** Coefficients. */
    private final double[][] a;
    /** First partial derivative along x. */
    private final BivariateFunction partialDerivativeX;
    /** First partial derivative along y. */
    private final BivariateFunction partialDerivativeY;
    /** Second partial derivative along x. */
    private final BivariateFunction partialDerivativeXX;
    /** Second partial derivative along y. */
    private final BivariateFunction partialDerivativeYY;
    /** Second crossed partial derivative. */
    private final BivariateFunction partialDerivativeXY;

    /**
     * Simple constructor.
     *
     * @param coeff Spline coefficients.
     * @param xR x spacing.
     * @param yR y spacing.
     * @param initializeDerivatives Whether to initialize the internal data
     * needed for calling any of the methods that compute the partial derivatives
     * this function.
     */
    BicubicFunction(double[] coeff,
                    double xR,
                    double yR,
                    boolean initializeDerivatives) {
        a = new double[N][N];
        for (int j = 0; j < N; j++) {
            final double[] aJ = a[j];
            for (int i = 0; i < N; i++) {
                aJ[i] = coeff[i * N + j];
            }
        }

        if (initializeDerivatives) {
            // Compute all partial derivatives functions.
            final double[][] aX = new double[N][N];
            final double[][] aY = new double[N][N];
            final double[][] aXX = new double[N][N];
            final double[][] aYY = new double[N][N];
            final double[][] aXY = new double[N][N];

            for (int i = 0; i < N; i++) {
                for (int j = 0; j < N; j++) {
                    final double c = a[i][j];
                    aX[i][j] = i * c;
                    aY[i][j] = j * c;
                    aXX[i][j] = (i - 1) * aX[i][j];
                    aYY[i][j] = (j - 1) * aY[i][j];
                    aXY[i][j] = j * aX[i][j];
                }
            }

            partialDerivativeX = (double x, double y) -> {
                final double x2 = x * x;
                final double[] pX = {0, 1, x, x2};

                final double y2 = y * y;
                final double y3 = y2 * y;
                final double[] pY = {1, y, y2, y3};

                return apply(pX, 1, pY, 0, aX) / xR;
            };
            partialDerivativeY = (double x, double y) -> {
                final double x2 = x * x;
                final double x3 = x2 * x;
                final double[] pX = {1, x, x2, x3};

                final double y2 = y * y;
                final double[] pY = {0, 1, y, y2};

                return apply(pX, 0, pY, 1, aY) / yR;
            };
            partialDerivativeXX = (double x, double y) -> {
                final double[] pX = {0, 0, 1, x};

                final double y2 = y * y;
                final double y3 = y2 * y;
                final double[] pY = {1, y, y2, y3};

                return apply(pX, 2, pY, 0, aXX) / (xR * xR);
            };
            partialDerivativeYY = (double x, double y) -> {
                final double x2 = x * x;
                final double x3 = x2 * x;
                final double[] pX = {1, x, x2, x3};

                final double[] pY = {0, 0, 1, y};

                return apply(pX, 0, pY, 2, aYY) / (yR * yR);
            };
            partialDerivativeXY = (double x, double y) -> {
                final double x2 = x * x;
                final double[] pX = {0, 1, x, x2};

                final double y2 = y * y;
                final double[] pY = {0, 1, y, y2};

                return apply(pX, 1, pY, 1, aXY) / (xR * yR);
            };
        } else {
            partialDerivativeX = null;
            partialDerivativeY = null;
            partialDerivativeXX = null;
            partialDerivativeYY = null;
            partialDerivativeXY = null;
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public double value(double x, double y) {
        if (x < 0 || x > 1) {
            throw new OutOfRangeException(x, 0, 1);
        }
        if (y < 0 || y > 1) {
            throw new OutOfRangeException(y, 0, 1);
        }

        final double x2 = x * x;
        final double x3 = x2 * x;
        final double[] pX = {1, x, x2, x3};

        final double y2 = y * y;
        final double y3 = y2 * y;
        final double[] pY = {1, y, y2, y3};

        return apply(pX, 0, pY, 0, a);
    }

    /**
     * Compute the value of the bicubic polynomial.
     *
     * <p>Assumes the powers are zero below the provided index, and 1 at the provided
     * index. This allows skipping some zero products and optimising multiplication
     * by one.
     *
     * @param pX Powers of the x-coordinate.
     * @param i Index of pX[i] == 1
     * @param pY Powers of the y-coordinate.
     * @param j Index of pX[j] == 1
     * @param coeff Spline coefficients.
     * @return the interpolated value.
     */
    private static double apply(double[] pX, int i, double[] pY, int j, double[][] coeff) {
        // assert pX[i] == 1
        double result = sumOfProducts(coeff[i], pY, j);
        while (++i < N) {
            final double r = sumOfProducts(coeff[i], pY, j);
            result += r * pX[i];
        }
        return result;
    }

    /**
     * Compute the sum of products starting from the provided index.
     * Assumes that factor {@code b[j] == 1}.
     *
     * @param a Factors.
     * @param b Factors.
     * @param j Index to initialise the sum.
     * @return the double
     */
    private static double sumOfProducts(double[] a, double[] b, int j) {
        // assert b[j] == 1
        final Sum sum = Sum.of(a[j]);
        while (++j < N) {
            sum.addProduct(a[j], b[j]);
        }
        return sum.getAsDouble();
    }

    /**
     * @return the partial derivative wrt {@code x}.
     */
    BivariateFunction partialDerivativeX() {
        return partialDerivativeX;
    }

    /**
     * @return the partial derivative wrt {@code y}.
     */
    BivariateFunction partialDerivativeY() {
        return partialDerivativeY;
    }

    /**
     * @return the second partial derivative wrt {@code x}.
     */
    BivariateFunction partialDerivativeXX() {
        return partialDerivativeXX;
    }

    /**
     * @return the second partial derivative wrt {@code y}.
     */
    BivariateFunction partialDerivativeYY() {
        return partialDerivativeYY;
    }

    /**
     * @return the second partial cross-derivative.
     */
    BivariateFunction partialDerivativeXY() {
        return partialDerivativeXY;
    }
}"""

b = "/*\n * Licensed to the Apache Software Foundation (ASF) under one or more\n * contributor license agreements.  See the NOTICE file distributed with\n * this work for additional information regarding copyright ownership.\n * The ASF licenses this file to You under the Apache License, Version 2.0\n * (the \"License\"); you may not use this file except in compliance with\n * the License.  You may obtain a copy of the License at\n *\n *      http://www.apache.org/licenses/LICENSE-2.0\n *\n * Unless required by applicable law or agreed to in writing, software\n * distributed under the License is distributed on an \"AS IS\" BASIS,\n * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n * See the License for the specific language governing permissions and\n * limitations under the License.\n */\npackage org.apache.commons.math4.legacy.analysis.interpolation;\n\nimport java.util.Arrays;\nimport java.util.function.DoubleBinaryOperator;\nimport java.util.function.Function;\n\nimport org.apache.commons.numbers.core.Sum;\nimport org.apache.commons.math4.legacy.analysis.BivariateFunction;\nimport org.apache.commons.math4.legacy.exception.DimensionMismatchException;\nimport org.apache.commons.math4.legacy.exception.NoDataException;\nimport org.apache.commons.math4.legacy.exception.NonMonotonicSequenceException;\nimport org.apache.commons.math4.legacy.exception.OutOfRangeException;\nimport org.apache.commons.math4.legacy.core.MathArrays;\n\n/**\n * Function that implements the\n * <a href=\"http://en.wikipedia.org/wiki/Bicubic_interpolation\">\n * bicubic spline interpolation</a>.\n *\n * @since 3.4\n */\npublic class BicubicInterpolatingFunction\n    implements BivariateFunction {\n    /** Number of coefficients. */\n    private static final int NUM_COEFF = 16;\n    /**\n     * Matrix to compute the spline coefficients from the function values\n     * and function derivatives values.\n     */\n    private static final double[][] AINV = {\n        { 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 },\n        { 0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0 },\n        { -3,3,0,0,-2,-1,0,0,0,0,0,0,0,0,0,0 },\n        { 2,-2,0,0,1,1,0,0,0,0,0,0,0,0,0,0 },\n        { 0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0 },\n        { 0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0 },\n        { 0,0,0,0,0,0,0,0,-3,3,0,0,-2,-1,0,0 },\n        { 0,0,0,0,0,0,0,0,2,-2,0,0,1,1,0,0 },\n        { -3,0,3,0,0,0,0,0,-2,0,-1,0,0,0,0,0 },\n        { 0,0,0,0,-3,0,3,0,0,0,0,0,-2,0,-1,0 },\n        { 9,-9,-9,9,6,3,-6,-3,6,-6,3,-3,4,2,2,1 },\n        { -6,6,6,-6,-3,-3,3,3,-4,4,-2,2,-2,-2,-1,-1 },\n        { 2,0,-2,0,0,0,0,0,1,0,1,0,0,0,0,0 },\n        { 0,0,0,0,2,0,-2,0,0,0,0,0,1,0,1,0 },\n        { -6,6,6,-6,-4,-2,4,2,-3,3,-3,3,-2,-1,-2,-1 },\n        { 4,-4,-4,4,2,2,-2,-2,2,-2,2,-2,1,1,1,1 }\n    };\n\n    /** Samples x-coordinates. */\n    private final double[] xval;\n    /** Samples y-coordinates. */\n    private final double[] yval;\n    /** Set of cubic splines patching the whole data grid. */\n    private final BicubicFunction[][] splines;\n\n    /**\n     * @param x Sample values of the x-coordinate, in increasing order.\n     * @param y Sample values of the y-coordinate, in increasing order.\n     * @param f Values of the function on every grid point.\n     * @param dFdX Values of the partial derivative of function with respect\n     * to x on every grid point.\n     * @param dFdY Values of the partial derivative of function with respect\n     * to y on every grid point.\n     * @param d2FdXdY Values of the cross partial derivative of function on\n     * every grid point.\n     * @throws DimensionMismatchException if the various arrays do not contain\n     * the expected number of elements.\n     * @throws NonMonotonicSequenceException if {@code x} or {@code y} are\n     * not strictly increasing.\n     * @throws NoDataException if any of the arrays has zero length.\n     */\n    public BicubicInterpolatingFunction(double[] x,\n                                        double[] y,\n                                        double[][] f,\n                                        double[][] dFdX,\n                                        double[][] dFdY,\n                                        double[][] d2FdXdY)\n        throws DimensionMismatchException,\n               NoDataException,\n               NonMonotonicSequenceException {\n        this(x, y, f, dFdX, dFdY, d2FdXdY, false);\n    }\n\n    /**\n     * @param x Sample values of the x-coordinate, in increasing order.\n     * @param y Sample values of the y-coordinate, in increasing order.\n     * @param f Values of the function on every grid point.\n     * @param dFdX Values of the partial derivative of function with respect\n     * to x on every grid point.\n     * @param dFdY Values of the partial derivative of function with respect\n     * to y on every grid point.\n     * @param d2FdXdY Values of the cross partial derivative of function on\n     * every grid point.\n     * @param initializeDerivatives Whether to initialize the internal data\n     * needed for calling any of the methods that compute the partial derivatives\n     * this function.\n     * @throws DimensionMismatchException if the various arrays do not contain\n     * the expected number of elements.\n     * @throws NonMonotonicSequenceException if {@code x} or {@code y} are\n     * not strictly increasing.\n     * @throws NoDataException if any of the arrays has zero length.\n     */\n    public BicubicInterpolatingFunction(double[] x,\n                                        double[] y,\n                                        double[][] f,\n                                        double[][] dFdX,\n                                        double[][] dFdY,\n                                        double[][] d2FdXdY,\n                                        boolean initializeDerivatives)\n        throws DimensionMismatchException,\n               NoDataException,\n               NonMonotonicSequenceException {\n        final int xLen = x.length;\n        final int yLen = y.length;\n\n        if (xLen == 0 || yLen == 0 || f.length == 0 || f[0].length == 0) {\n            throw new NoDataException();\n        }\n        if (xLen != f.length) {\n            throw new DimensionMismatchException(xLen, f.length);\n        }\n        if (xLen != dFdX.length) {\n            throw new DimensionMismatchException(xLen, dFdX.length);\n        }\n        if (xLen != dFdY.length) {\n            throw new DimensionMismatchException(xLen, dFdY.length);\n        }\n        if (xLen != d2FdXdY.length) {\n            throw new DimensionMismatchException(xLen, d2FdXdY.length);\n        }\n\n        MathArrays.checkOrder(x);\n        MathArrays.checkOrder(y);\n\n        xval = x.clone();\n        yval = y.clone();\n\n        final int lastI = xLen - 1;\n        final int lastJ = yLen - 1;\n        splines = new BicubicFunction[lastI][lastJ];\n\n        for (int i = 0; i < lastI; i++) {\n            if (f[i].length != yLen) {\n                throw new DimensionMismatchException(f[i].length, yLen);\n            }\n            if (dFdX[i].length != yLen) {\n                throw new DimensionMismatchException(dFdX[i].length, yLen);\n            }\n            if (dFdY[i].length != yLen) {\n                throw new DimensionMismatchException(dFdY[i].length, yLen);\n            }\n            if (d2FdXdY[i].length != yLen) {\n                throw new DimensionMismatchException(d2FdXdY[i].length, yLen);\n            }\n            final int ip1 = i + 1;\n            final double xR = xval[ip1] - xval[i];\n            for (int j = 0; j < lastJ; j++) {\n                final int jp1 = j + 1;\n                final double yR = yval[jp1] - yval[j];\n                final double xRyR = xR * yR;\n                final double[] beta = new double[] {\n                    f[i][j], f[ip1][j], f[i][jp1], f[ip1][jp1],\n                    dFdX[i][j] * xR, dFdX[ip1][j] * xR, dFdX[i][jp1] * xR, dFdX[ip1][jp1] * xR,\n                    dFdY[i][j] * yR, dFdY[ip1][j] * yR, dFdY[i][jp1] * yR, dFdY[ip1][jp1] * yR,\n                    d2FdXdY[i][j] * xRyR, d2FdXdY[ip1][j] * xRyR, d2FdXdY[i][jp1] * xRyR, d2FdXdY[ip1][jp1] * xRyR\n                };\n\n                splines[i][j] = new BicubicFunction(computeSplineCoefficients(beta),\n                                                    xR,\n                                                    yR,\n                                                    initializeDerivatives);\n            }\n        }\n    }\n\n    /**\n     * {@inheritDoc}\n     */\n    @Override\n    public double value(double x, double y)\n        throws OutOfRangeException {\n        final int i = searchIndex(x, xval);\n        final int j = searchIndex(y, yval);\n\n        final double xN = (x - xval[i]) / (xval[i + 1] - xval[i]);\n        final double yN = (y - yval[j]) / (yval[j + 1] - yval[j]);\n\n        return splines[i][j].value(xN, yN);\n    }\n\n    /**\n     * Indicates whether a point is within the interpolation range.\n     *\n     * @param x First coordinate.\n     * @param y Second coordinate.\n     * @return {@code true} if (x, y) is a valid point.\n     */\n    public boolean isValidPoint(double x, double y) {\n        return !(x < xval[0] ||\n            x > xval[xval.length - 1] ||\n            y < yval[0] ||\n            y > yval[yval.length - 1]);\n    }\n\n    /**\n     * @return the first partial derivative respect to x.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    public DoubleBinaryOperator partialDerivativeX() {\n        return partialDerivative(BicubicFunction::partialDerivativeX);\n    }\n\n    /**\n     * @return the first partial derivative respect to y.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    public DoubleBinaryOperator partialDerivativeY() {\n        return partialDerivative(BicubicFunction::partialDerivativeY);\n    }\n\n    /**\n     * @return the second partial derivative respect to x.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    public DoubleBinaryOperator partialDerivativeXX() {\n        return partialDerivative(BicubicFunction::partialDerivativeXX);\n    }\n\n    /**\n     * @return the second partial derivative respect to y.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    public DoubleBinaryOperator partialDerivativeYY() {\n        return partialDerivative(BicubicFunction::partialDerivativeYY);\n    }\n\n    /**\n     * @return the second partial cross derivative.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    public DoubleBinaryOperator partialDerivativeXY() {\n        return partialDerivative(BicubicFunction::partialDerivativeXY);\n    }\n\n    /**\n     * @param which derivative function to apply.\n     * @return the selected partial derivative.\n     * @throws NullPointerException if the internal data were not initialized\n     * (cf. {@link #BicubicInterpolatingFunction(double[],double[],double[][],\n     *             double[][],double[][],double[][],boolean) constructor}).\n     */\n    private DoubleBinaryOperator partialDerivative(Function<BicubicFunction, BivariateFunction> which) {\n        return (x, y) -> {\n            final int i = searchIndex(x, xval);\n            final int j = searchIndex(y, yval);\n\n            final double xN = (x - xval[i]) / (xval[i + 1] - xval[i]);\n            final double yN = (y - yval[j]) / (yval[j + 1] - yval[j]);\n\n            return which.apply(splines[i][j]).value(xN, yN);\n        };\n    }\n\n    /**\n     * @param c Coordinate.\n     * @param val Coordinate samples.\n     * @return the index in {@code val} corresponding to the interval\n     * containing {@code c}.\n     * @throws OutOfRangeException if {@code c} is out of the\n     * range defined by the boundary values of {@code val}.\n     */\n    private static int searchIndex(double c, double[] val) {\n        final int r = Arrays.binarySearch(val, c);\n\n        if (r == -1 ||\n            r == -val.length - 1) {\n            throw new OutOfRangeException(c, val[0], val[val.length - 1]);\n        }\n\n        if (r < 0) {\n            // \"c\" in within an interpolation sub-interval: Return the\n            // index of the sample at the lower end of the sub-interval.\n            return -r - 2;\n        }\n        final int last = val.length - 1;\n        if (r == last) {\n            // \"c\" is the last sample of the range: Return the index\n            // of the sample at the lower end of the last sub-interval.\n            return last - 1;\n        }\n\n        // \"c\" is another sample point.\n        return r;\n    }\n\n    /**\n     * Compute the spline coefficients from the list of function values and\n     * function partial derivatives values at the four corners of a grid\n     * element. They must be specified in the following order:\n     * <ul>\n     *  <li>f(0,0)</li>\n     *  <li>f(1,0)</li>\n     *  <li>f(0,1)</li>\n     *  <li>f(1,1)</li>\n     *  <li>f<sub>x</sub>(0,0)</li>\n     *  <li>f<sub>x</sub>(1,0)</li>\n     *  <li>f<sub>x</sub>(0,1)</li>\n     *  <li>f<sub>x</sub>(1,1)</li>\n     *  <li>f<sub>y</sub>(0,0)</li>\n     *  <li>f<sub>y</sub>(1,0)</li>\n     *  <li>f<sub>y</sub>(0,1)</li>\n     *  <li>f<sub>y</sub>(1,1)</li>\n     *  <li>f<sub>xy</sub>(0,0)</li>\n     *  <li>f<sub>xy</sub>(1,0)</li>\n     *  <li>f<sub>xy</sub>(0,1)</li>\n     *  <li>f<sub>xy</sub>(1,1)</li>\n     * </ul>\n     * where the subscripts indicate the partial derivative with respect to\n     * the corresponding variable(s).\n     *\n     * @param beta List of function values and function partial derivatives\n     * values.\n     * @return the spline coefficients.\n     */\n    private static double[] computeSplineCoefficients(double[] beta) {\n        final double[] a = new double[NUM_COEFF];\n\n        for (int i = 0; i < NUM_COEFF; i++) {\n            double result = 0;\n            final double[] row = AINV[i];\n            for (int j = 0; j < NUM_COEFF; j++) {\n                result += row[j] * beta[j];\n            }\n            a[i] = result;\n        }\n\n        return a;\n    }\n}\n\n/**\n * Bicubic function.\n */\nclass BicubicFunction implements BivariateFunction {\n    /** Number of points. */\n    private static final short N = 4;\n    /** Coefficients. */\n    private final double[][] a;\n    /** First partial derivative along x. */\n    private final BivariateFunction partialDerivativeX;\n    /** First partial derivative along y. */\n    private final BivariateFunction partialDerivativeY;\n    /** Second partial derivative along x. */\n    private final BivariateFunction partialDerivativeXX;\n    /** Second partial derivative along y. */\n    private final BivariateFunction partialDerivativeYY;\n    /** Second crossed partial derivative. */\n    private final BivariateFunction partialDerivativeXY;\n\n    /**\n     * Simple constructor.\n     *\n     * @param coeff Spline coefficients.\n     * @param xR x spacing.\n     * @param yR y spacing.\n     * @param initializeDerivatives Whether to initialize the internal data\n     * needed for calling any of the methods that compute the partial derivatives\n     * this function.\n     */\n    BicubicFunction(double[] coeff,\n                    double xR,\n                    double yR,\n                    boolean initializeDerivatives) {\n        a = new double[N][N];\n        for (int j = 0; j < N; j++) {\n            final double[] aJ = a[j];\n            for (int i = 0; i < N; i++) {\n                aJ[i] = coeff[i * N + j];\n            }\n        }\n\n        if (initializeDerivatives) {\n            // Compute all partial derivatives functions.\n            final double[][] aX = new double[N][N];\n            final double[][] aY = new double[N][N];\n            final double[][] aXX = new double[N][N];\n            final double[][] aYY = new double[N][N];\n            final double[][] aXY = new double[N][N];\n\n            for (int i = 0; i < N; i++) {\n                for (int j = 0; j < N; j++) {\n                    final double c = a[i][j];\n                    aX[i][j] = i * c;\n                    aY[i][j] = j * c;\n                    aXX[i][j] = (i - 1) * aX[i][j];\n                    aYY[i][j] = (j - 1) * aY[i][j];\n                    aXY[i][j] = j * aX[i][j];\n                }\n            }\n\n            partialDerivativeX = (double x, double y) -> {\n                final double x2 = x * x;\n                final double[] pX = {0, 1, x, x2};\n\n                final double y2 = y * y;\n                final double y3 = y2 * y;\n                final double[] pY = {1, y, y2, y3};\n\n                return apply(pX, 1, pY, 0, aX) / xR;\n            };\n            partialDerivativeY = (double x, double y) -> {\n                final double x2 = x * x;\n                final double x3 = x2 * x;\n                final double[] pX = {1, x, x2, x3};\n\n                final double y2 = y * y;\n                final double[] pY = {0, 1, y, y2};\n\n                return apply(pX, 0, pY, 1, aY) / yR;\n            };\n            partialDerivativeXX = (double x, double y) -> {\n                final double[] pX = {0, 0, 1, x};\n\n                final double y2 = y * y;\n                final double y3 = y2 * y;\n                final double[] pY = {1, y, y2, y3};\n\n                return apply(pX, 2, pY, 0, aXX) / (xR * xR);\n            };\n            partialDerivativeYY = (double x, double y) -> {\n                final double x2 = x * x;\n                final double x3 = x2 * x;\n                final double[] pX = {1, x, x2, x3};\n\n                final double[] pY = {0, 0, 1, y};\n\n                return apply(pX, 0, pY, 2, aYY) / (yR * yR);\n            };\n            partialDerivativeXY = (double x, double y) -> {\n                final double x2 = x * x;\n                final double[] pX = {0, 1, x, x2};\n\n                final double y2 = y * y;\n                final double[] pY = {0, 1, y, y2};\n\n                return apply(pX, 1, pY, 1, aXY) / (xR * yR);\n            };\n        } else {\n            partialDerivativeX = null;\n            partialDerivativeY = null;\n            partialDerivativeXX = null;\n            partialDerivativeYY = null;\n            partialDerivativeXY = null;\n        }\n    }\n\n    /**\n     * {@inheritDoc}\n     */\n    @Override\n    public double value(double x, double y) {\n        if (x < 0 || x > 1) {\n            throw new OutOfRangeException(x, 0, 1);\n        }\n        if (y < 0 || y > 1) {\n            throw new OutOfRangeException(y, 0, 1);\n        }\n\n        final double x2 = x * x;\n        final double x3 = x2 * x;\n        final double[] pX = {1, x, x2, x3};\n\n        final double y2 = y * y;\n        final double y3 = y2 * y;\n        final double[] pY = {1, y, y2, y3};\n\n        return apply(pX, 0, pY, 0, a);\n    }\n\n    /**\n     * Compute the value of the bicubic polynomial.\n     *\n     * <p>Assumes the powers are zero below the provided index, and 1 at the provided\n     * index. This allows skipping some zero products and optimising multiplication\n     * by one.\n     *\n     * @param pX Powers of the x-coordinate.\n     * @param i Index of pX[i] == 1\n     * @param pY Powers of the y-coordinate.\n     * @param j Index of pX[j] == 1\n     * @param coeff Spline coefficients.\n     * @return the interpolated value.\n     */\n    private static double apply(double[] pX, int i, double[] pY, int j, double[][] coeff) {\n        // assert pX[i] == 1\n        double result = sumOfProducts(coeff[i], pY, j);\n        while (++i < N) {\n            final double r = sumOfProducts(coeff[i], pY, j);\n            result += r * pX[i];\n        }\n        return result;\n    }\n\n    /**\n     * Compute the sum of products starting from the provided index.\n     * Assumes that factor {@code b[j] == 1}.\n     *\n     * @param a Factors.\n     * @param b Factors.\n     * @param j Index to initialise the sum.\n     * @return the double\n     */\n    private static double sumOfProducts(double[] a, double[] b, int j) {\n        // assert b[j] == 1\n        final Sum sum = Sum.of(a[j]);\n        while (++j < N) {\n            sum.addProduct(a[j], b[j]);\n        }\n        return sum.getAsDouble();\n    }\n\n    /**\n     * @return the partial derivative wrt {@code x}.\n     */\n    BivariateFunction partialDerivativeX() {\n        return partialDerivativeX;\n    }\n\n    /**\n     * @return the partial derivative wrt {@code y}.\n     */\n    BivariateFunction partialDerivativeY() {\n        return partialDerivativeY;\n    }\n\n    /**\n     * @return the second partial derivative wrt {@code x}.\n     */\n    BivariateFunction partialDerivativeXX() {\n        return partialDerivativeXX;\n    }\n\n    /**\n     * @return the second partial derivative wrt {@code y}.\n     */\n    BivariateFunction partialDerivativeYY() {\n        return partialDerivativeYY;\n    }\n\n    /**\n     * @return the second partial cross-derivative.\n     */\n    BivariateFunction partialDerivativeXY() {\n        return partialDerivativeXY;\n    }\n}"


def line_col_to_char_index(text, start_line, start_column, end_line, end_column):
    lines = text.split('\n')
    start_index = sum(len(lines[i]) + 1 for i in range(start_line - 1)) + start_column - 1
    end_index = sum(len(lines[i]) + 1 for i in range(end_line - 1)) + end_column - 1
    return start_index, end_index

start_index, end_index  = line_col_to_char_index(b, 367, 0, 582, 2)

print("start_index:", start_index)
print("end_index:", end_index)