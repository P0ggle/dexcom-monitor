import React, { useEffect, useState } from 'react';

function App() {
  const [data, setData] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState(null);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('access_token');
    if (token) {
      setAccessToken(token);
      fetchDateRange(token);
    }
  }, []);

  const authenticateWithDexcom = () => {
    window.location.href = '/api/dexcom/auth';
  };

  const fetchDateRange = (token) => {
    fetch(`/api/dexcom/daterange?access_token=${token}`)
      .then(response => response.json())
      .then(data => {
        setDateRange(data);
        fetchDexcomData(token, data);
      })
      .catch(error => setError(error));
  };

  const fetchDexcomData = (token, dateRange) => {
    const startDate = dateRange.egvs.start.systemTime;
    const endDate = dateRange.egvs.end.systemTime;
    fetch(`/api/dexcom/data?access_token=${token}&startDate=${startDate}&endDate=${endDate}`)
      .then(response => response.json())
      .then(data => setData(data))
      .catch(error => setError(error));
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Dexcom Glucose Data</h1>
        {error && <p>Error: {error.message}</p>}
        {!accessToken && (
          <button onClick={authenticateWithDexcom}>
            Authenticate with Dexcom
          </button>
        )}
        {data ? (
          <div>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        ) : (
          <p>Loading...</p>
        )}
      </header>
    </div>
  );
}

export default App;
