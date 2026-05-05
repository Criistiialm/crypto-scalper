import pandas as pd
import numpy as np
import pytz

class SMCEngine:
    """
    Motor de análisis de Smart Money Concepts.
    Se alimenta con un DataFrame OHLCV y detecta ineficiencias y quiebres.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Asegurarnos de que el índice es datetime para el Session Manager
        if not isinstance(self.df.index, pd.DatetimeIndex):
            if 'timestamp' in self.df.columns:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                self.df.set_index('timestamp', inplace=True)
        
        # Convertir a zona horaria ART si es tz-naive o convertir si es otra
        if getattr(self.df.index, "tz", None) is None:
            self.df.index = self.df.index.tz_localize('UTC').tz_convert('America/Argentina/Buenos_Aires')
        else:
            self.df.index = self.df.index.tz_convert('America/Argentina/Buenos_Aires')

    def apply_time_session(self):
        """
        SKILL: Time & Session Manager
        Filtra setups en la ventana 03:30 AM a 13:30 PM ART.
        Marca los altos y bajos formados antes de las 03:30 AM como "Liquidez Asiática".
        """
        df = self.df
        df['is_tradable'] = False
        df['is_asian_session'] = False
        
        # Obtener horas y minutos
        hours = df.index.hour
        mins = df.index.minute
        time_in_minutes = hours * 60 + mins
        
        start_trade_min = 3 * 60 + 30  # 03:30 AM
        end_trade_min = 13 * 60 + 30   # 13:30 PM
        
        # Ventana operativa
        df['is_tradable'] = (time_in_minutes >= start_trade_min) & (time_in_minutes < end_trade_min)
        
        # Sesión Asiática (desde las 00:00 hasta las 03:30)
        df['is_asian_session'] = (time_in_minutes < start_trade_min)
        
        return df

    def identify_swings(self, window=3):
        """
        Identifica Swing Highs y Swing Lows en la estructura.
        Un Swing High requiere 'window' velas más bajas a izquierda y derecha.
        """
        df = self.df
        df['is_swing_high'] = False
        df['is_swing_low'] = False

        for i in range(window, len(df) - window):
            # Swing High
            if all(df['high'].iloc[i] > df['high'].iloc[i-window:i]) and \
               all(df['high'].iloc[i] > df['high'].iloc[i+1:i+window+1]):
                df.at[df.index[i], 'is_swing_high'] = True

            # Swing Low
            if all(df['low'].iloc[i] < df['low'].iloc[i-window:i]) and \
               all(df['low'].iloc[i] < df['low'].iloc[i+1:i+window+1]):
                df.at[df.index[i], 'is_swing_low'] = True

        return df

    def identify_fvg(self):
        """
        Identifica Fair Value Gaps (FVG).
        FVG Alcista: Low de la vela 3 > High de la vela 1.
        FVG Bajista: High de la vela 3 < Low de la vela 1.
        """
        df = self.df
        df['fvg_bullish'] = False
        df['fvg_bearish'] = False
        
        for i in range(2, len(df)):
            # FVG Bullish
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                df.at[df.index[i-1], 'fvg_bullish'] = True
            
            # FVG Bearish
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                df.at[df.index[i-1], 'fvg_bearish'] = True
                
        return df

    def identify_structure(self):
        """
        SKILL: SMC & Market Structure
        Detecta BOS (Break of Structure) y CHoCH (Change of Character).
        Requiere que el precio cierre (close) por encima/debajo del swing.
        """
        df = self.df
        df['bos'] = 0   # 1 para BOS alcista, -1 para BOS bajista
        df['choch'] = 0 # 1 para CHoCH alcista, -1 para CHoCH bajista
        
        last_swing_high = None
        last_swing_low = None
        trend = 1 # Asumimos tendencia alcista inicial
        
        for i in range(len(df)):
            idx = df.index[i]
            
            # Actualizamos swings recientes
            if df['is_swing_high'].iloc[i]:
                last_swing_high = df['high'].iloc[i]
            if df['is_swing_low'].iloc[i]:
                last_swing_low = df['low'].iloc[i]
                
            close_price = df['close'].iloc[i]
            
            # Rompimientos alcistas
            if last_swing_high is not None and close_price > last_swing_high:
                if trend == 1:
                    df.at[idx, 'bos'] = 1 # Continuación
                else:
                    df.at[idx, 'choch'] = 1 # Cambio de carácter
                    trend = 1
                # Invalidamos el swing roto
                last_swing_high = None
                
            # Rompimientos bajistas
            elif last_swing_low is not None and close_price < last_swing_low:
                if trend == -1:
                    df.at[idx, 'bos'] = -1 # Continuación
                else:
                    df.at[idx, 'choch'] = -1 # Cambio de carácter
                    trend = -1
                # Invalidamos el swing roto
                last_swing_low = None
                
        return df

    def analyze(self):
        """
        Ejecuta todo el análisis estructural de la temporalidad.
        """
        self.df = self.apply_time_session()
        self.df = self.identify_swings()
        self.df = self.identify_fvg()
        self.df = self.identify_structure()
        return self.df

if __name__ == "__main__":
    print("Probando SMCEngine con datos ficticios...")
    # Generamos un df dummy con fechas
    dates = pd.date_range(start='2026-05-05 01:00:00', periods=100, freq='15min', tz='UTC')
    data = {
        'open': np.random.randn(100) + 100,
        'high': np.random.randn(100) + 102,
        'low': np.random.randn(100) + 98,
        'close': np.random.randn(100) + 100
    }
    df = pd.DataFrame(data, index=dates)
    engine = SMCEngine(df)
    res = engine.analyze()
    print("Velas en sesión operable:", res['is_tradable'].sum())
    print("Velas en sesión asiática:", res['is_asian_session'].sum())
    print("Swings High encontrados:", res['is_swing_high'].sum())
    print("Swings Low encontrados:", res['is_swing_low'].sum())
    print("FVGs Bullish:", res['fvg_bullish'].sum())
    print("FVGs Bearish:", res['fvg_bearish'].sum())
    print("BOS Detectados:", (res['bos'] != 0).sum())
    print("CHoCH Detectados:", (res['choch'] != 0).sum())
