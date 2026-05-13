import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import Input from '../../components/Input/Input';
import Button from '../../components/Button/Button';
import styles from '../Auth/Auth.module.css';

const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('As senhas nao coincidem.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password, name }),
      });

      const data = await response.json();
      const message = data?.error?.message || data?.message;

      if (response.ok) {
        navigate('/login');
      } else {
        setError(message || 'Erro ao registrar usuario.');
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
            <UserPlus size={32} className={styles.logoIcon} />
          </div>
          <h1 className={styles.title}>Criar Conta</h1>
          <p className={styles.subtitle}>Junte-se ao HydraSensor</p>
        </div>

        <form onSubmit={handleRegister} className={styles.form}>
          <Input
            label="Nome"
            type="text"
            placeholder="Seu nome completo"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="E-mail / Usuario"
            type="text"
            placeholder="usuario"
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
          <Input
            label="Confirmar Senha"
            type="password"
            placeholder="********"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {error && <div className={styles.errorMessage}>{error}</div>}

          <Button type="submit" fullWidth className={styles.submitBtn} disabled={loading}>
            {loading ? 'Cadastrando...' : 'Cadastrar'}
          </Button>
        </form>

        <div className={styles.footer}>
          Ja tem uma conta? <Link to="/login" className={styles.link}>Faca login</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
