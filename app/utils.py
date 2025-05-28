class FinancialGoalOptimizer:
    def __init__(self, transactions):
        self.transactions = transactions
        self.period_factors = {
            'daily': 365,
            'weekly': 52,
            'monthly': 12,
            'yearly': 1
        }
    
    def calculate_total_net(self, years):
        """Calculate the TOTAL net savings (income - expenses) over N years"""
        total = 0
        for period, annual_factor in self.period_factors.items():
            income = sum(self.transactions['income'].get(period, [])) * annual_factor * years
            expense = sum(self.transactions['expense'].get(period, [])) * annual_factor * years
            total += (income - expense)
        return total
    
    def find_optimal_years(self, goalamount, learning_rate=0.0001, max_iter=1000, tolerance=1.0):
        """Find years required to minimize |goalamount - total_net|"""
        years = 1.0  # Initial guess
        prev_error = float('inf')
        
        for iteration in range(max_iter):
            total_net = self.calculate_total_net(years)
            error = goalamount - total_net
            
            if abs(error) < tolerance:
                break
            
            # Calculate gradient
            delta = 0.001 * years
            perturbed_net = self.calculate_total_net(years + delta)
            gradient = (perturbed_net - total_net) / delta
            gradient = max(min(gradient, 1e6), -1e6)
            
            # Update years
            years += learning_rate * error * gradient
            years = max(0.1, min(years, 100))  # Keep within reasonable bounds
            
            # Adjust learning rate if error increases
            if abs(error) > prev_error:
                learning_rate *= 0.9
                
            prev_error = abs(error)
            
            if iteration % 100 == 0:
                print(f"Iter {iteration}: years={years:.3f}, net=${total_net:,.2f}, error=${error:,.2f}")
        
        return years