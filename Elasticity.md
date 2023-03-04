
# Price elasticity

If $Q$ represents the quantity of anything (jobs, goods, either supply or demand)
$$\theta\,[\,x\,](x_{t+1}, x_{t})\coloneqq \left[\dfrac{Q(x_{t+1}) - Q(x_{t})}{Q(x_{t+1}) + Q(x_{t})}\right]\left[\dfrac{P(x_{t+1}) - P(x_{t})}{P(x_{t+1}) + P(x_{t})}\right]^{-1}
$$
Or in a less notation  heavy way: 
$$\theta\,[\,x\,] = \dfrac{\Delta Q(x)}{Q(x)}\dfrac{P(x)}{\Delta P(x)}$$

Finally, if you have an estimate already, you can predict new values as

$$\theta\cdot Q \cdot \Delta P = P \cdot \Delta Q $$
This gives us

$$Q_{t+1}=-\frac{-Q_{t}P_{t+1}-Q_{t}P_{t}-\theta\cdot Q_{t}P_{t+1}+\theta\cdot Q_{t}P_{t}}{P_{t+1}+P_{t}-\theta\cdot P_{t+1}+\theta\cdot P_{t}};\quad $$
Or in terms of price delta percentage $\Delta\text{Perc}[\,P\,] = \Delta P / P$

$$
Q_{t+1}=\frac{-Q_{t}-\theta\cdot Q_{t}\cdot\Delta\text{Perc}[\,P\,]}{\theta\cdot\Delta\text{Perc}[\,P\,]-1}
$$

## Employment elasticity w.r.t MW

In the above equation, the min wage $w_\mu$ is just the price of labor $P(x)$
Employment is the quantity $Q$ , i.e. the quantity of demand for labor

Hence the elasticity estimate becomes