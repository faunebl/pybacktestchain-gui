import numpy as np
from scipy.optimize import minimize
from datetime import datetime
from typing import Dict
from pybacktestchain.broker import FirstTwoMoments
import logging

class EqualRiskContributionStrategy(FirstTwoMoments):
    def compute_portfolio(self, t: datetime, information_set: Dict):
        try:
            Sigma = information_set['covariance_matrix']
            n = Sigma.shape[0]

            def risk_contribution(weights):
                portfolio_variance = weights.T @ Sigma @ weights
                marginal_contribution = Sigma @ weights
                risk_contributions = weights * marginal_contribution
                return risk_contributions / portfolio_variance

            def obj(weights):
                rc = risk_contribution(weights)
                return np.sum((rc - 1 / n)**2)

            cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = [(0.0, 1.0)] * n
            x0 = np.ones(n) / n

            res = minimize(obj, x0, constraints=cons, bounds=bounds)

            if res.success:
                return dict(zip(information_set['companies'], res.x))
            else:
                raise Exception("Optimization did not converge")
        except Exception as e:
            logging.warning("Error computing portfolio, returning equal weight portfolio")
            logging.warning(e)
            return {k: 1/len(information_set['companies']) for k in information_set['companies']}


class MaximumDiversificationStrategy(FirstTwoMoments):
    def compute_portfolio(self, t: datetime, information_set: Dict):
        try:
            Sigma = information_set['covariance_matrix']
            vol = np.sqrt(np.diag(Sigma))
            n = len(vol)

            def obj(weights):
                portfolio_vol = np.sqrt(weights.T @ Sigma @ weights)
                return -np.sum(weights * vol) / portfolio_vol

            cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = [(0.0, 1.0)] * n
            x0 = np.ones(n) / n

            res = minimize(obj, x0, constraints=cons, bounds=bounds)

            if res.success:
                return dict(zip(information_set['companies'], res.x))
            else:
                raise Exception("Optimization did not converge")
        except Exception as e:
            logging.warning("Error computing portfolio, returning equal weight portfolio")
            logging.warning(e)
            return {k: 1/len(information_set['companies']) for k in information_set['companies']}


class MinimumVarianceStrategy(FirstTwoMoments):
    def compute_portfolio(self, t: datetime, information_set: Dict):
        try:
            Sigma = information_set['covariance_matrix']
            n = Sigma.shape[0]

            def obj(weights):
                return weights.T @ Sigma @ weights

            cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = [(0.0, 1.0)] * n
            x0 = np.ones(n) / n

            res = minimize(obj, x0, constraints=cons, bounds=bounds)

            if res.success:
                return dict(zip(information_set['companies'], res.x))
            else:
                raise Exception("Optimization did not converge")
        except Exception as e:
            logging.warning("Error computing portfolio, returning equal weight portfolio")
            logging.warning(e)
            return {k: 1/len(information_set['companies']) for k in information_set['companies']}


class MomentumBasedStrategy(FirstTwoMoments):
    def compute_information(self, t: datetime):
        data = self.slice_data(t)
        information_set = {}

        data['return'] = data.groupby(self.company_column)[self.adj_close_column].pct_change()
        momentum = data.groupby(self.company_column)['return'].mean()

        information_set['momentum'] = momentum.to_numpy()
        information_set['companies'] = momentum.index.to_numpy()
        return information_set

    def compute_portfolio(self, t: datetime, information_set: Dict):
        momentum = information_set['momentum']
        weights = momentum / np.sum(momentum)
        return dict(zip(information_set['companies'], weights))


class SectorNeutralPortfolio(FirstTwoMoments):
    def compute_information(self, t: datetime):
        data = self.slice_data(t)
        information_set = {}

        data['return'] = data.groupby(self.company_column)[self.adj_close_column].pct_change()
        expected_return = data.groupby(self.company_column)['return'].mean()
        covariance_matrix = data.pivot(index=self.time_column, columns=self.company_column, values=self.adj_close_column).cov()

        information_set['expected_return'] = expected_return
        information_set['covariance_matrix'] = covariance_matrix
        information_set['sectors'] = data.groupby(self.company_column)['sector'].first()
        information_set['companies'] = expected_return.index.to_numpy()
        return information_set

    def compute_portfolio(self, t: datetime, information_set: Dict):
        Sigma = information_set['covariance_matrix']
        sectors = information_set['sectors']
        n = len(sectors)

        def sector_constraint(sector):
            return {'type': 'eq', 'fun': lambda x: np.sum(x[sectors == sector]) - 1 / len(np.unique(sectors))}

        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}] + [sector_constraint(s) for s in np.unique(sectors)]
        bounds = [(0.0, 1.0)] * n
        x0 = np.ones(n) / n

        res = minimize(lambda x: x.T @ Sigma @ x, x0, constraints=cons, bounds=bounds)
        return dict(zip(information_set['companies'], res.x)) if res.success else {k: 1/n for k in information_set['companies']}


class DrawdownControlStrategy(FirstTwoMoments):
    def compute_information(self, t: datetime):
        data = self.slice_data(t)
        information_set = {}

        data['return'] = data.groupby(self.company_column)[self.adj_close_column].pct_change()
        data['cumulative_return'] = (1 + data['return']).groupby(data[self.company_column]).cumprod()
        data['drawdown'] = data['cumulative_return'] / data['cumulative_return'].cummax() - 1

        max_drawdown = data.groupby(self.company_column)['drawdown'].min()
        information_set['max_drawdown'] = max_drawdown
        information_set['companies'] = max_drawdown.index.to_numpy()
        return information_set

    def compute_portfolio(self, t: datetime, information_set: Dict):
        drawdown = information_set['max_drawdown']
        weights = 1 / (1 - drawdown)
        weights /= np.sum(weights)
        return dict(zip(information_set['companies'], weights))
