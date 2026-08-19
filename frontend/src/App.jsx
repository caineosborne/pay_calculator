import React from 'react';
import { PayProvider } from './context/PayContext';
import { Layout } from './components/Layout/Layout';
import { InputDetails } from './components/Config/InputDetails';
import { ShiftCalculator } from './components/Config/ShiftCalculator';
import ShiftTable from './components/DisplayTables/ShiftTable';
import SummaryTable from './components/DisplayTables/SummaryTable';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <PayProvider>
        <ShiftCalculator>
          <Layout>
            <main className="workspace">
              <InputDetails />
              <ShiftTable />
              <SummaryTable />
            </main>
          </Layout>
        </ShiftCalculator>
      </PayProvider>
    </AuthProvider>
  );
}

export default App;
