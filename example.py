#  Python 2.7 file for Numerical Methods II, Spring 2016
#  http://www.math.nyu.edu/faculty/goodman/teaching/NumericalMethodsII2016/index.html

#  File: HeatEquationAnimation.py

#  Solve the heat equation and make a movie of the solution

#  Type: python HeatEquationAnimation.py   ... and hope for the best

import numpy                as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot    as plt
import matplotlib.animation as ani

print "Making a movie in python!  Got popcorn?"


#     Physical parameters describing the problem


L = 3                  # length of the computational domain
T = 1                  #  final time for integration
D = 2.                 #  the diffusion coefficient

L = float(L)           #  So calculations don't get rounded incorrectly
T = float(T)           #  So calculations don't get rounded incorrectly
D = float(D)           #  So calculations don't get rounded incorrectly

xb    = L/3            #  parameters defining a gaussian initial condition, the mean
sig   = L/10           #  the standard deviation
sigsq = sig*sig

#         Numerical parameters

n  = 100                    # number of interior points in the x direction
Tf = .002                  # physical time interval between movie frames

Nframes = int( T / Tf)+1   # the number of frames up to time T, rounded up
Tf      = T / Nframes      # Adjust the time per frame to fit the number of frames.

dx = L / float(n+1)        #  n+1 = the number of intervals defined by n+2 points
dt = .9*(dx*dx)/(2*D)      #  time step, for stability, plus a "haircut" to avoid ringing

print "Nframes = " + str(Nframes) + ", T = " + str(T) + ", Tf = " + str(Tf) + ", dx = " + str(dx)

Nf = int( Tf/dt) + 1       #  The number of time steps per frame, rounded up
dt = Tf/Nf                 #  Adjust the time step down because Nf was rounded up

u  = np.ndarray(n+2)       #  u[0] and u[n+1] hold boundary values that are not updated
v  = np.ndarray(n+2)       #  the solution at the next time
xa = np.ndarray(n+2)       #  a list of x values, for plotting
for i in range(0,n+2):
    xa[i] = i*dx


#    Initial data

for i in range(1,n+1):
    x = i*dx
#    u[i] = np.sin(np.pi*x/L)
    u[i] = np.exp( -.5*(x - xb)*(x-xb)/sigsq)



#     boundary conditions, set once for both u and v

u[0]   = 0.
u[n+1] = 0.
v[0  ] = 0.
v[n+1] = 0.

#       Set up the movie camera

FFMpegWriter = ani.writers['ffmpeg']
metadata     = dict( title  = 'Heat equation', artist='Matplotlib',
                     comment= 'solution of the heat equation')
writer       = FFMpegWriter(fps=15, metadata=metadata)

fig          = plt.figure()
l,           = plt.plot([])
plt.xlim(0, L)
plt.ylim(0, 1)
plt.grid(True)


#      The loop over frames: advance one frame then record the answer

C = dt*D/(dx*dx)

with writer.saving(fig, "HeatEquation.mp4", Nframes):

    for frame in range(0,Nframes):
        print "frame " + str(frame)

#    Take all the time steps to advance to the next frame

        for k in range(0,Nf):
    
#    Loop over the grid points.  Apply the finite difference operator.

            for k in range(1,n+1):  #  omit the first and last grid points,...
                                    #  ... which have boundarh conditions
                v[k] = u[k] + C*( u[k+1] - 2*u[k] + u[k-1])

            for k in range(1,n+1):  #   copy from v back to u, omit boundary values.

                u[k] = v[k]

        t = Tf*(frame+1)

        l.set_data(xa,u)
        title = ( "time %7.3f" % ((frame+1)*Tf) ) + ( ", frame %4d" % frame ) + (", n %4d" % n)
        plt.title(title)
        writer.grab_frame()














