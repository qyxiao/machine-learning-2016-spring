function [T,W,x] = SolveODE(n, times, a, d, method);

   h=1/n; % Grid spacing
   x=([1:n]-0.5)*h; % Cell centers
   u0=sin(pi*x).^100; % Initial condition

   Aw_plus_g = @(t,w) AdvDiff(t, w, h, a, d, method);

   % Read ode solver documentation!
   % Specifying tspan with more than two elements
   % has little effect on the efficiency of computation
   % but for large systems, affects memory management.
   options = odeset('RelTol',1e-3); % Not too tight of a tolerance
   [T,W] = ode23(Aw_plus_g, times, u0, options);

end
