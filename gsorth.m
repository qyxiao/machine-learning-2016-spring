function q = gsorth(a);
% GSORTH Gram-Schmidt orthogonalisation

n = size(a,1);  m = size(a,2); q = a;
for k = 1:m,
  q(:,k) = q(:,k)./sqrt(sum(q(:,k).^2));
  for j = k+1:m,
    q(:,j) = q(:,j) - sum(q(:,k).*q(:,j)).*q(:,k); 
  end,
end,
