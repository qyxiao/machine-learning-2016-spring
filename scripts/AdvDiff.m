function Aw_plus_g = Advection1(t, w, h, a, d, method) % Evaluate rhs of ODE w'=A*w+g(t)
   % Finite volume spatial discretization to solve:
   % u_t+a*u_x=d*u_xx
   % with Dirichlet BCs on left and Neumann on right:
   % u(0,t)=sin(-pi*t)^100;
   % u_x(1,t)=0 if d>0
   % If there were only advection the solution would be u(x,t)=sin(pi*(x-t))^100
   
   w0=sin(pi*(0-t))^100; % Dirichlet BC at left
   
   n=length(w);

   % Fluxes start on left-most and end on right-most face
   fluxes=zeros(n+1,1); % MATLAB requires column vectors for ode solvers
         
   % Compute advective fluxes first, ignoring BCs at outflow boundary
   switch abs(method)
      case 0 % upwind
      
         fluxes(2:n+1) = a*w(1:n);
         fluxes(1) = a*w0; % Left-most face
      
      case 1 % centered in interior, upwind at right boundary
         
         fluxes(2:n)=0.5*a*(w(1:n-1)+w(2:n));
         fluxes(1)=a*w0;         
         fluxes(n+1)=a*w(n); % Upwind at right-most face
         
      case 2 % Third-order upwind biased
      
         fluxes(3:n) = a*(-w(1:n-2)+5*w(2:n-1)+2*w(3:n))/6;
         
         % Left boundary
         wm1=w0; % Extrapolate beyond the boundary using constant extrapolation
         fluxes(1) = a*w0;  
         fluxes(2) = a*(-wm1+5*w(1)+2*w(2))/6;
         
         % Right boundary
         if(method>0) % Use upwinding at the right boundary
            fluxes(n+1)=a*w(n); % Upwind at right-most face
         else
            wnp1=w(n); % Extrapolate beyond the boundary using linear extrapolation
            % Observe that here using the BC would give the same ghost value
            % But this would be different for Dirichlet BC at the right boundary!
            fluxes(n+1) = a*(-w(n-1)+5*w(n)+2*wnp1)/6;
         end   
         
      otherwise
         error('method=%d not implemented yet',method);  
   end
   
   if(d>0) % Add diffusive fluxes
      % In the interior we use the usual three-point centered difference:
      fluxes(2:n)=fluxes(2:n) - d*(w(2:n)-w(1:n-1))/h;
      
      fluxes(1)=fluxes(1) - (w(1)-w0)/(0.5*h); % Dirichlet BC at left
      % Neumann BC at right means no diffusive contribution to fluxes(n+1)   
   end
   
   Aw_plus_g =  (fluxes(1:n)-fluxes(2:n+1))/h;

end
