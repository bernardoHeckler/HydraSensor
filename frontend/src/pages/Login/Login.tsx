import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import Input from '../../components/Input/Input';
import Button from '../../components/Button/Button';
import styles from '../Auth/Auth.module.css';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password }),
      });

      const data = await response.json();
      const message = data?.error?.message || data?.message;

      if (response.ok) {
        if (data?.data?.token) {
          localStorage.setItem('token', data.data.token);
        }

        navigate('/dashboard');
      } else {
        setError(message || 'Credenciais invalidas.');
      }
    } catch (err) {
      setError('Erro ao conectar com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.logoWrapper}>
            <Shield size={32} className={styles.logoIcon} />
          </div>
          <h1 className={styles.title}>HydraSensor</h1>
          <p className={styles.subtitle}>Faca login para acessar o painel</p>
        </div>

        <form onSubmit={handleLogin} className={styles.form}>
          <Input
            label="Usuario / E-mail"
            type="text"
            placeholder="admin"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Senha"
            type="password"
            placeholder="********"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <div className={styles.errorMessage}>{error}</div>}

          <Button type="submit" fullWidth className={styles.submitBtn} disabled={loading}>
            {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>

        <div className={styles.footer}>
          Nao tem uma conta? <Link to="/register" className={styles.link}>Cadastre-se</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
