import React from 'react';
import { PayProvider } from './context/PayContext';
import { Layout } from './components/Layout/Layout';
import { InputDetails } from './components/Config/InputDetails';
import { ShiftCalculator } from './components/Config/ShiftCalculator';
import ShiftTable from './components/DisplayTables/ShiftTable';
import SummaryTable from './components/DisplayTables/SummaryTable';

function App() {
  return (
    <PayProvider>
      <ShiftCalculator>
        <Layout>
          <div className="space-y-6">
            <InputDetails />
            <ShiftTable />
            <SummaryTable />
          </div>
        </Layout>
      </ShiftCalculator>
    </PayProvider>
  );
}

export default App;