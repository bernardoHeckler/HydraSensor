import React from 'react';
import clsx from 'clsx';
import styles from './Button.module.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  fullWidth = false,
  className,
  ...props 
}) => {
  return (
    <button 
      className={clsx(
        styles.button, 
        styles[variant], 
        fullWidth && styles.fullWidth,
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
