import React, { useEffect, useState } from 'react';
import { api } from '../../services/apis';

export function RuleConfigurationEditor({
    configurationId,
    onConfigurationSaved,
}) {
    const [configuration, setConfiguration] = useState(null);
    const [source, setSource] = useState('');
    const [copyName, setCopyName] = useState('');
    const [message, setMessage] = useState('');
    const [isWorking, setIsWorking] = useState(false);

    useEffect(() => {
        let isMounted = true;

        const loadSource = async () => {
            if (!configurationId) {
                return;
            }
            setConfiguration(null);
            setSource('');
            setIsWorking(true);
            setMessage('');
            try {
                const loadedConfiguration =
                    await api.getRuleConfiguration(configurationId);
                if (isMounted) {
                    setConfiguration(loadedConfiguration);
                    setSource(loadedConfiguration.source);
                    setCopyName(
                        loadedConfiguration.kind === 'builtin'
                            ? `${loadedConfiguration.name} Custom`
                            : ''
                    );
                }
            } catch (error) {
                if (isMounted) {
                    setMessage(error.message);
                }
            } finally {
                if (isMounted) {
                    setIsWorking(false);
                }
            }
        };

        loadSource();
        return () => {
            isMounted = false;
        };
    }, [configurationId]);

    const validateSource = async () => {
        if (!configuration) {
            return;
        }
        setIsWorking(true);
        setMessage('');
        try {
            await api.validateRuleConfiguration(
                configuration.base_award,
                source
            );
            setMessage('Valid Python rule class. Ready to save.');
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsWorking(false);
        }
    };

    const saveSource = async () => {
        if (!configuration) {
            return;
        }
        setIsWorking(true);
        setMessage('');
        try {
            let savedConfiguration;
            if (configuration.kind === 'builtin') {
                savedConfiguration = await api.createRuleConfiguration(
                    configuration.base_award,
                    copyName,
                    source
                );
            } else {
                savedConfiguration = await api.updateRuleConfiguration(
                    configuration.id,
                    source
                );
            }
            setMessage('Custom configuration saved and selected.');
            await onConfigurationSaved(savedConfiguration);
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsWorking(false);
        }
    };

    if (!configurationId) {
        return null;
    }

    return (
        <div className="mt-4 rounded-lg border border-gray-200 dark:border-gray-600 p-4 text-left">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h3 className="m-0 text-base font-semibold text-gray-900 dark:text-white">
                        Python rule configuration
                    </h3>
                    <p className="mt-1 mb-0 text-xs text-gray-600 dark:text-gray-300">
                        {configuration?.kind === 'builtin'
                            ? 'This built-in is read-only. Saving creates a separate custom file.'
                            : 'This is an editable custom file stored on this server.'}
                    </p>
                </div>
                <span className="rounded bg-gray-100 dark:bg-gray-700 px-2 py-1 text-xs uppercase">
                    {configuration?.kind || 'loading'}
                </span>
            </div>

            {configuration?.kind === 'builtin' && (
                <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                        New custom configuration name
                    </label>
                    <input
                        type="text"
                        value={copyName}
                        onChange={(event) => setCopyName(event.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm dark:bg-gray-700 dark:text-white"
                    />
                </div>
            )}

            <label className="mt-3 block text-sm font-medium text-gray-700 dark:text-gray-200">
                Rule class source
            </label>
            <textarea
                value={source}
                onChange={(event) => setSource(event.target.value)}
                spellCheck="false"
                disabled={isWorking}
                className="mt-1 block h-96 w-full resize-y rounded-md border border-gray-300 bg-gray-950 p-3 font-mono text-xs text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />

            <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                    type="button"
                    onClick={validateSource}
                    disabled={isWorking || !configuration}
                    className="bg-gray-100 text-gray-700 hover:bg-gray-200"
                >
                    Validate
                </button>
                <button
                    type="button"
                    onClick={saveSource}
                    disabled={
                        isWorking ||
                        !configuration ||
                        (configuration.kind === 'builtin' && !copyName.trim())
                    }
                    className="bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                    {configuration?.kind === 'builtin'
                        ? 'Save custom copy'
                        : 'Save changes'}
                </button>
                {message && (
                    <span className="text-sm text-gray-700 dark:text-gray-200">
                        {message}
                    </span>
                )}
            </div>
        </div>
    );
}
