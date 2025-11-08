import React from 'react'
import { useState } from 'react';

const FormField = ({ id, label, type = 'text', value, onChange, placeholder, as = 'input', options = [] }: FormFieldProps) => {
    const InputToRender = ({ type }: { type: string } ) => {
        if (type === 'textarea') {
            return <textarea 
                id={id}
                name={id}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
            />
        } else if (type === 'select') {
            return <select 
                id={id}
                name={id}
                value={value}
                onChange={onChange}

            >
                {options.map(({ label, value }) => ( <option key={label} value={value}>{label}</option> ))}
            </select>
        } else if (type === 'search') {

            const [isDropdownOpen, setIsDropdownOpen] = useState(false);
            const [selected, setSelected] = useState<string|null>(null);

            const filteredOptions = options.filter(option =>
                option.label.toLowerCase().includes(value.toLowerCase())
            );

            const handleSelect = (optionValue: string) => {
                setSelected(optionValue);
                setIsDropdownOpen(false);
            };

            return (
            <div className="relative w-full">   
                <input className="w-full"
                    type='text'
                    id={id}
                    name={id}
                    value={selected || value}
                    onChange={onChange}
                    placeholder={placeholder}
                    onClick={() => setIsDropdownOpen(true)}
                />
                    {isDropdownOpen && (
                        <ul className='dropdown'>
                            {filteredOptions.length > 0 ? (
                                filteredOptions.map(({ label, value }) => (
                                    <li className="list-item" key={label} onClick={() => handleSelect(value)}>{label}</li>
                                ))
                            ) : (
                                <li>No player found</li>
                            )}
                        </ul>
                    )}
            </div> )

        } else {
            return <input 
                type={type}
                id={id}
                name={id}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
            />
        }
    }
    return (
        <div className='form-field'>
            <label htmlFor={id}>{label}</label>
            <InputToRender type={as} />
        </div>
    )
}

export default FormField