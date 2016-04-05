from core.stack import *
from core.coreclasses import Strategy

class MeanReversionPairsStrategy(Strategy):
    """
    Pairs trading mean reversion strategy using Bollinger Bands.
    Compute hedge ratio on a rolling basis with lookback window.
    Go long/short the spread when it's below/above the entry threshold,
    exit position when spread is less than exit threshold.
    """
    def __init__(self, window=None, zentry=None, zexit=None):
        if window is None:
            raise ValueError, "Need to choose a lookback window"
        if zentry is None or zexit is None:
            raise ValueError, "Need to choose an entry/exit z-score"
        if window == -1:
            print "\nWARNING: Performing regression over entire time frame",
            print "- lookahead bias!\n"
        self.window = window
        self.zentry = zentry
        self.zexit = zexit
        print "\nRunning strategy with parameters:"
        print "\tWindow:", self.window
        print "\tEntry z:", self.zentry
        print "\tExit z:", self.zexit
        print "\n"

    def begin(self):
        if len(self.symbols) != 2:
            raise ValueError, "Can only handle two assets"

    def generate_signals(self):
        signals = pd.DataFrame(index=self.prices.index, columns=self.prices.columns)

        x_prices = self.prices.iloc[:, 0]
        y_prices = self.prices.iloc[:, 1]

        if self.window == -1:
            ols_res = pd.ols(y=y_prices, x=x_prices)
        else:
            ols_res = pd.ols(y=y_prices, x=x_prices, window=self.window)

        beta = ols_res.beta.x
        spread_mean_ols = ols_res.beta.intercept

        spread = y_prices - beta * x_prices
        
        #mymean = pd.rolling_mean(y_prices,self.window) - beta*pd.rolling_mean(x_prices,self.window)
        if self.window == -1:
            spread_mean = spread.mean() 
            spread_std  = spread.std()
        else:
            spread_mean = pd.rolling_mean(spread, self.window) #not same because beta is changing
            spread_std  = pd.rolling_std (spread, self.window)

        z_score = (spread - spread_mean) / spread_std
        #z_score = (spread - spread_mean_ols) / spread_std # gives weird result

        longs  = z_score < -self.zentry
        shorts = z_score > self.zentry
        exits  = abs(z_score) < self.zexit

        #FIXME: should be in hedge ratio
        signals.loc[longs , :] = np.array( ([-1, 1],)*len(signals[longs])  )
        signals.loc[shorts, :] = np.array( ([ 1,-1],)*len(signals[shorts]) )
        signals.loc[exits , :] = np.array( ([ 0, 0],)*len(signals[exits])  )

        if self.options.debug:
            #self.debug_output()
            plt.scatter(x_prices,y_prices); plt.show()
            if self.window != -1:
                beta.plot(); plt.show()
            spread.plot(); plt.show()
            z_score.plot(); plt.show()
        
        return signals

    def debug_output(self):
        pass