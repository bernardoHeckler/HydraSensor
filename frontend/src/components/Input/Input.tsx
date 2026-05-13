import React, { forwardRef } from 'react';
import clsx from 'clsx';
import styles from './Input.module.css';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ label, error, className, ...props }, ref) => {
  return (
    <div className={clsx(styles.wrapper, className)}>
      {label && <label className={styles.label}>{label}</label>}
      <input 
        ref={ref}
        className={clsx(styles.input, error && styles.inputError)} 
        {...props} 
      />
      {error && <span className={styles.error}>{error}</span>}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
