import { ReactNode } from 'react';

type PaddingSize = 'sm' | 'md' | 'lg';

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  padding?: PaddingSize;
}

const paddingClasses: Record<PaddingSize, string> = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export default function Card({
  title,
  children,
  className = '',
  padding = 'md',
}: CardProps) {
  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 shadow-sm ${paddingClasses[padding]} ${className}`}
    >
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      {children}
    </div>
  );
}
