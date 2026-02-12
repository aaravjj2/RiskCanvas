import math
from models.pricing import black_scholes_call
S,K,T,r,sigma = 40.0,40.0,0.25,0.03,0.2
num = (math.log(S/K) + (r + 0.5 * sigma ** 2) * T)
den = (sigma * math.sqrt(T))
d1 = num/den
d2 = d1 - sigma * math.sqrt(T)
N = lambda x: 0.5*(1.0 + math.erf(x/math.sqrt(2.0)))
print('num',num,'den',den,'d1',d1,'d2',d2)
print('N(d1)',N(d1),'N(d2)',N(d2))
print('call calc', S*N(d1) - K*math.exp(-r*T)*N(d2))
print('module call', black_scholes_call(S,K,T,r,sigma))
