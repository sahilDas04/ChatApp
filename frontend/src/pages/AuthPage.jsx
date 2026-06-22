import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { errMsg } from '../api/client';

export default function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('login');

  // Login state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPass, setLoginPass] = useState('');
  const [loginErr, setLoginErr] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Register state
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPass, setRegPass] = useState('');
  const [regPass2, setRegPass2] = useState('');
  const [regErr, setRegErr] = useState('');
  const [regSuccess, setRegSuccess] = useState('');
  const [regLoading, setRegLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginErr('');
    setLoginLoading(true);
    try {
      await login(loginEmail, loginPass);
      navigate('/dashboard');
    } catch (err) {
      setLoginErr(errMsg(err));
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegErr('');
    setRegSuccess('');
    if (regPass !== regPass2) { setRegErr('Passwords do not match.'); return; }
    setRegLoading(true);
    try {
      await register(regUsername, regEmail, regPass);
      setRegSuccess('✅ Account created! Please log in.');
      setTab('login');
      setLoginEmail(regEmail);
    } catch (err) {
      setRegErr(errMsg(err));
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>💬 ChatShare</h1>
          <p>Secure file sharing &amp; real‑time chat</p>
        </div>

        <div className="tabs">
          <button className={`tab-btn${tab === 'login' ? ' active' : ''}`} onClick={() => setTab('login')}>
            🔑 Login
          </button>
          <button className={`tab-btn${tab === 'register' ? ' active' : ''}`} onClick={() => setTab('register')}>
            📝 Register
          </button>
        </div>

        {/* Login */}
        {tab === 'login' && (
          <form onSubmit={handleLogin}>
            {regSuccess && <div className="alert alert-success">{regSuccess}</div>}
            {loginErr && <div className="alert alert-error">⚠️ {loginErr}</div>}
            <div className="form-group">
              <label>Email</label>
              <input className="form-input" type="email" placeholder="you@example.com"
                value={loginEmail} onChange={e => setLoginEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input className="form-input" type="password" placeholder="Your password"
                value={loginPass} onChange={e => setLoginPass(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full mt-2" type="submit" disabled={loginLoading}>
              {loginLoading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        )}

        {/* Register */}
        {tab === 'register' && (
          <form onSubmit={handleRegister}>
            {regErr && <div className="alert alert-error">⚠️ {regErr}</div>}
            <div className="form-group">
              <label>Username</label>
              <input className="form-input" type="text" placeholder="cooluser123"
                value={regUsername} onChange={e => setRegUsername(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input className="form-input" type="email" placeholder="you@example.com"
                value={regEmail} onChange={e => setRegEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input className="form-input" type="password" placeholder="Min 8 chars, 1 uppercase, 1 digit"
                value={regPass} onChange={e => setRegPass(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Confirm Password</label>
              <input className="form-input" type="password" placeholder="Repeat password"
                value={regPass2} onChange={e => setRegPass2(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full mt-2" type="submit" disabled={regLoading}>
              {regLoading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
