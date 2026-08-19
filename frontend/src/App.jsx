import React from 'react';
import { PayProvider } from './context/PayContext';
import { Layout } from './components/Layout/Layout';
import { InputDetails } from './components/Config/InputDetails';
import { ShiftCalculator } from './components/Config/ShiftCalculator';
import ShiftTable from './components/DisplayTables/ShiftTable';
import SummaryTable from './components/DisplayTables/SummaryTable';
import { AuthProvider } from './context/AuthContext';
import { usePay } from './context/PayContext';
import AcademicCalculator from './components/Academic/AcademicCalculator';

function CalculatorWorkspace() {
  const { state } = usePay();

  if (state.config.calculatorMode === 'academic_activity') {
    return (
      <main className="workspace academic-workspace">
        <AcademicCalculator scheme={state.config.academicScheme || 'qut_sessional'} />
      </main>
    );
  }

  return (
    <main className="workspace">
      <InputDetails />
      <ShiftTable />
      <SummaryTable />
    </main>
  );
}

function App() {
  return (
    <AuthProvider>
      <PayProvider>
        <ShiftCalculator>
          <Layout>
            <CalculatorWorkspace />
          </Layout>
        </ShiftCalculator>
      </PayProvider>
    </AuthProvider>
  );
}

export default App;
