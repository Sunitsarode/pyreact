export const getApiURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const apiURL = `${protocol}//${hostname}:5001/api`;
    console.log('🔗 API URL:', apiURL);
    return apiURL;
  }
  return 'http://localhost:5001/api';
};

export const API_URL = getApiURL();