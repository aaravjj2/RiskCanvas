import math

S=40.0;K=40.0;T=0.25;r=0.03

def call_price(S,K,T,r,sigma,q=0.0):
    if sigma==0 or T==0:
        return max(S*math.exp(-q*T)-K*math.exp(-r*T), 0.0)
    d1=(math.log(S/K)+(r-q+0.5*sigma*sigma)*T)/(sigma*math.sqrt(T))
    d2=d1-sigma*math.sqrt(T)
    N=lambda x:0.5*(1.0+math.erf(x/math.sqrt(2.0)))
    return S*math.exp(-q*T)*N(d1)-K*math.exp(-r*T)*N(d2)

best=(999,None,None)
for sigma in [i/1000.0 for i in range(50,501)]:
    c=call_price(S,K,T,r,sigma,0.0)
    err=abs(c-2.07)
    if err<best[0]:
        best=(err,sigma,c)

print('best sigma:',best)

best_q=(999,None,None)
for q in [i/1000.0 for i in range(0,101)]:
    c=call_price(S,K,T,r,0.2,q)
    err=abs(c-2.07)
    if err<best_q[0]:
        best_q=(err,q,c)
print('best q:',best_q)
