import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import AppBody from './AppBody';
import { useEffect, useState } from 'react';


function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [authenticationError, setAuthenticationError] = useState(false);

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        const response = await fetch('/userinfo', { credentials: 'include' });
        if (!response.ok) {
          throw new Error(`Authentication check failed (${response.status})`);
        }

        const { user } = await response.json();
        if (user) {
          setAuthenticated(true);
        } else {
          window.location.assign('/login');
        }
      } catch (error) {
        console.error('Could not check authentication', error);
        setAuthenticationError(true);
      }
    };

    checkAuthentication();
  }, []);

  if (authenticationError) {
    return (
      <div className="alert alert-danger m-4" role="alert">
        The authentication service is temporarily unavailable. Please try again.
      </div>
    );
  }

  return authenticated ? <AppBody /> : null;
}

export default App;
