// // components/DisplayTables/ShiftTimeInput.jsx
// import React from 'react';
// import { usePay } from '../../context/PayContext';

// export default function ShiftTimeInput({ shift, idx, handleChange }) {
//     const { state } = usePay();

//     const handleTimeChange = (field, value, isInput = false) => {
//         let newValue;

//         if (field === 'break_duration') {
//             newValue = value === '' ? shift.break_duration :
//                 Math.max(0, Math.min(24, parseFloat(value) || 0)).toString();
//         } else if (isInput) {
//             newValue = value === '' ? shift[field] :
//                 Math.min(23, Math.max(0, parseInt(value) || 0)).toString();
//         } else {
//             const currentValue = parseInt(shift[field]) || 0;
//             if (value === 'increment') {
//                 newValue = Math.min(23, currentValue + 1).toString();
//             } else if (value === 'decrement') {
//                 newValue = Math.max(0, currentValue - 1).toString();
//             }
//         }
//         handleChange(idx, field, newValue);
//     };

//     const clearDay = () => {
//         handleChange(idx, 'start', '');
//         handleChange(idx, 'end', '');
//         handleChange(idx, 'break_duration', '0.5');
//     };

//     // Get daily calculations from state
//     const dailyBreakdown = state.calculations.dailyBreakdown?.[shift.day] || {
//         ordinary: 0,
//         overtime: 0,
//         total: 0,
//         pay: 0
//     };

//     return (
//         <tr className="hover:bg-gray-50">
//             <td className="px-2 py-1 whitespace-nowrap text-sm font-medium text-gray-900">
//                 {shift.day}
//             </td>
//             <td className="px-2 py-1 whitespace-nowrap">
//                 <div className="flex items-center space-x-1">
//                     <button
//                         onClick={() => handleTimeChange('start', 'decrement')}
//                         className="p-1 text-gray-500 hover:text-gray-700"
//                     >
//                         -
//                     </button>
//                     <input
//                         type="number"
//                         value={shift.start}
//                         onChange={(e) => handleTimeChange('start', e.target.value, true)}
//                         className="w-16 p-1 text-center border rounded"
//                         min="0"
//                         max="23"
//                     />
//                     <button
//                         onClick={() => handleTimeChange('start', 'increment')}
//                         className="p-1 text-gray-500 hover:text-gray-700"
//                     >
//                         +
//                     </button>
//                 </div>
//             </td>
//             <td className="px-2 py-1 whitespace-nowrap">
//                 <div className="flex items-center space-x-1">
//                     <button
//                         onClick={() => handleTimeChange('end', 'decrement')}
//                         className="p-1 text-gray-500 hover:text-gray-700"
//                     >
//                         -
//                     </button>
//                     <input
//                         type="number"
//                         value={shift.end}
//                         onChange={(e) => handleTimeChange('end', e.target.value, true)}
//                         className="w-16 p-1 text-center border rounded"
//                         min="0"
//                         max="23"
//                     />
//                     <button
//                         onClick={() => handleTimeChange('end', 'increment')}
//                         className="p-1 text-gray-500 hover:text-gray-700"
//                     >
//                         +
//                     </button>
//                 </div>
//             </td>
//             <td className="px-2 py-1 whitespace-nowrap">
//                 <div className="flex items-center space-x-1">
//                     <input
//                         type="number"
//                         value={shift.break_duration}
//                         onChange={(e) => handleTimeChange('break_duration', e.target.value, true)}
//                         className="w-16 p-1 text-center border rounded"
//                         step="0.5"
//                         min="0"
//                         max="24"
//                     />
//                     <button
//                         onClick={clearDay}
//                         className="ml-2 px-2 py-0.5 bg-gray-200 rounded text-xs hover:bg-gray-300"
//                         title="Clear times"
//                     >
//                         Clear
//                     </button>
//                 </div>
//             </td>
//             <td className="px-2 py-1 whitespace-nowrap text-sm">
//                 <span className="text-gray-900">
//                     {dailyBreakdown.ordinary || '0'}
//                 </span>
//                 {dailyBreakdown.overtime > 0 && (
//                     <span className="text-red-600 ml-2">
//                         (+{dailyBreakdown.overtime})
//                     </span>
//                 )}
//             </td>
//             <td className="px-2 py-1 whitespace-nowrap text-sm text-blue-600">
//                 ${dailyBreakdown.pay || '0'}
//             </td>
//         </tr>
//     );
// }