% Finite volume spatial discretization to solve:
% u_t+a*u_x=d*u_xx
% with Dirichlet BCs on left and Neumann on right:
% u(0,t)=sin(-pi*t)^100;
% u_x(1,t)=0 if d>0
% If there were only advection the solution would be u(x,t)=sin(pi*(x-t))^100

clear
format short; format compact

% method=0 upwind
% method=1 centered difference
% method=2 third-order upwind biased (or -2 for a slight variant)
method=1 % Choose method

times=[0, 0.25, 0.5, 0.75]; % What times to output the solution at

% Choose advection and diffusion coefficients
a=1;
%d=0 % Advection only
d=0.001

n=128; % Choose desired resolution

h=1/n; % Grid spacing
x=([1:n]-0.5)*h; % Cell centers

% Compute an accurate solution for comparison:
if d<=0 % We know the exact solution here
   u_exact=zeros(3,n);
   for i=2:length(times)
      u_exact(i-1,:)=sin(pi*(x-times(i))).^100;
   end
   x_exact=x;
else % Just use a refined computation to get the 'exact' solution
   n_max=256;
   [T_exact,W_exact,x_exact] = SolveODE(n_max, times, a, d, -2);
   u_exact=W_exact(2:4,:);
end   

[T,W,x] = SolveODE(n, times, a, d, method);

figure(1); clf

plot(x, W(2,:), 'r-'); hold on; % Numerical solution
plot(x_exact, u_exact(1,:), 'r--'); hold on; % Exact solution

plot(x, W(3,:), 'g-'); hold on; % Numerical solution
plot(x_exact, u_exact(2,:), 'g--'); hold on; % Exact solution

plot(x, W(4,:), 'b-'); hold on; % Numerical solution
plot(x_exact, u_exact(3,:), 'b--'); hold on; % Exact solution
