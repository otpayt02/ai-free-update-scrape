import { Theme } from './settings/types';
import { SignalConsole } from './components/generated/SignalConsole';

let theme: Theme = 'dark';

function App() {
  function setTheme(theme: Theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  setTheme(theme);

  return (
    <>
      <SignalConsole />
    </>
  ); // %EXPORT_STATEMENT%
}

export default App;
