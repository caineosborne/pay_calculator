// // components/DisplayTables/ShiftResults.jsx
// import React from 'react';
// import { usePay } from '../../context/PayContext';

// export default function ShiftResults() {
//     const { state } = usePay();

//     console.log('ShiftResults state:', state); // Debug log

//     return (
//         <tr className="bg-gray-50 font-semibold">
//             <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
//                 Totals
//             </td>
//             <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
//                 {state.calculations.ordinaryHours || '-'} hrs
//             </td>
//             <td className="px-2 py-2 whitespace-nowrap text-sm text-red-600">
//                 {state.calculations.overtimeHours || '-'} hrs
//             </td>
//             <td className="px-2 py-2 whitespace-nowrap text-sm text-blue-600">
//                 ${state.payments.totalPay || '-'}
//             </td>
//         </tr>
//     );
// }